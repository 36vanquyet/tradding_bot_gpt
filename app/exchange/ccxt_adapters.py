from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Sequence

try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover
    ccxt = None

from app.config.settings import ExchangeCredentials
from app.core.models import Order, Position, SymbolRule, Trade
from app.exchange.base import ExchangeAdapter

logger = logging.getLogger(__name__)


@dataclass
class CCXTAdapter(ExchangeAdapter):
    name: str
    creds: ExchangeCredentials
    exchange_cls_name: str
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    positions: Dict[str, Position] = field(default_factory=dict)
    open_orders: Dict[str, Order] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if ccxt is None:
            raise RuntimeError("ccxt is not installed")
        cls = getattr(ccxt, self.exchange_cls_name)
        self.client = cls(
            {
                "apiKey": self.creds.api_key,
                "secret": self.creds.api_secret,
                "enableRateLimit": True,
                "options": {
                    "adjustForTimeDifference": True,
                    "recvWindow": 10000,
                    "recv_window": 10000,
                },
            }
        )
        if self.creds.testnet and hasattr(self.client, "set_sandbox_mode"):
            self.client.set_sandbox_mode(True)
        self._markets_loaded = False
        if hasattr(self.client, "load_time_difference"):
            try:
                self.client.load_time_difference()
            except Exception:
                pass

    def _call_with_retry(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        last_exc: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # pragma: no cover
                last_exc = exc
                transient = isinstance(exc, (getattr(ccxt, "NetworkError", Exception), getattr(ccxt, "RequestTimeout", Exception), getattr(ccxt, "ExchangeNotAvailable", Exception)))
                if attempt >= self.retry_attempts or not transient:
                    raise
                time.sleep(self.retry_delay_seconds * attempt)
        if last_exc is not None:
            raise last_exc

    def _ensure_markets(self) -> None:
        if not self._markets_loaded:
            self._call_with_retry(self.client.load_markets)
            self._markets_loaded = True

    def _market_kind_for_symbol(self, symbol: str, market_kind: str = "spot") -> str:
        self._ensure_markets()
        market = self.client.market(symbol)
        if market.get("spot"):
            return "spot"
        if market.get("swap") or market.get("future") or market.get("contract"):
            return "future"
        return market_kind

    def _order_params(self, symbol: str, market_kind: str) -> dict[str, Any]:
        kind = self._market_kind_for_symbol(symbol, market_kind)
        if self.name != "bybit":
            return {}
        market = self.client.market(symbol)
        if kind == "spot":
            return {"category": "spot"}
        if market.get("linear"):
            return {"category": "linear"}
        if market.get("inverse"):
            return {"category": "inverse"}
        return {"category": "linear"}

    def _fetch_positions_for_symbols(self, symbols: Sequence[str]) -> list[dict[str, Any]]:
        if not symbols or not hasattr(self.client, "fetch_positions"):
            return []
        params = self._order_params(symbols[0], "future")
        return list(self._call_with_retry(self.client.fetch_positions, list(symbols), params))

    def _fetch_open_orders_for_symbol(self, symbol: str) -> list[dict[str, Any]]:
        params = self._order_params(symbol, self._market_kind_for_symbol(symbol))
        return list(self._call_with_retry(self.client.fetch_open_orders, symbol, None, None, params))

    @staticmethod
    def _is_min_amount_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "must be greater than minimum amount precision" in message
            or "must be greater than minimum amount" in message
            or "minimum amount precision" in message
        )

    def configure_futures(self, symbol: str, margin_mode: str | None = None, leverage: float | None = None) -> None:
        if self._market_kind_for_symbol(symbol, "future") != "future":
            return
        params = self._order_params(symbol, "future")
        if margin_mode and hasattr(self.client, "set_margin_mode"):
            try:
                self._call_with_retry(self.client.set_margin_mode, margin_mode, symbol, params)
            except Exception as exc:
                message = str(exc).lower()
                if "same" not in message and "not modified" not in message and "110026" not in message:
                    raise
        if leverage and hasattr(self.client, "set_leverage"):
            try:
                self._call_with_retry(self.client.set_leverage, leverage, symbol, params)
            except TypeError:
                leverages = {"buyLeverage": str(leverage), "sellLeverage": str(leverage), **params}
                self._call_with_retry(self.client.set_leverage, leverage, symbol, leverages)
            except Exception as exc:
                message = str(exc).lower()
                if "same" not in message and "not modified" not in message and "110043" not in message:
                    raise

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list[list[float]]:
        self._ensure_markets()
        return self._call_with_retry(self.client.fetch_ohlcv, symbol, timeframe=timeframe, limit=limit)

    def fetch_balance_quote(self, quote: str = "USDT", market_kind: str = "spot") -> float:
        self._ensure_markets()
        params: dict[str, Any] = {}
        if self.name == "bybit" and market_kind == "future":
            params = {"type": "swap"}
        balance = self._call_with_retry(self.client.fetch_balance, params)
        free_bal = balance.get("free", {})
        total_bal = balance.get("total", {})
        return float(free_bal.get(quote) or total_bal.get(quote) or 0.0)

    def fetch_symbol_rule(self, symbol: str) -> SymbolRule:
        self._ensure_markets()
        market = self.client.market(symbol)
        limits = market.get("limits", {})
        amount_limits = limits.get("amount", {}) or {}
        cost_limits = limits.get("cost", {}) or {}
        precision = market.get("precision", {}) or {}
        min_qty = float(amount_limits.get("min") or 0.0)
        min_notional = float(cost_limits.get("min") or 0.0)
        amount_precision = precision.get("amount")
        step_size = 10 ** (-int(amount_precision)) if isinstance(amount_precision, int) else max(min_qty, 0.0001)
        return SymbolRule(
            min_qty=min_qty or step_size,
            step_size=step_size,
            min_notional=min_notional or 5.0,
        )

    def fetch_ticker_price(self, symbol: str) -> float:
        self._ensure_markets()
        ticker = self._call_with_retry(self.client.fetch_ticker, symbol)
        return float(ticker.get("last") or ticker.get("close") or 0.0)

    def _trade_from_order(self, symbol: str, side: str, quantity: float, order: dict[str, Any], order_type: str) -> Trade:
        avg_price = float(order.get("average") or order.get("price") or self.fetch_ticker_price(symbol))
        fee_cost = 0.0
        fees = order.get("fees") or []
        if fees:
            fee_cost = sum(float(x.get("cost") or 0.0) for x in fees)
        elif order.get("fee"):
            fee_cost = float((order.get("fee") or {}).get("cost") or 0.0)
        return Trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=avg_price,
            fee=fee_cost,
            mode="live",
            order_type=order_type,
            status=str(order.get("status") or "filled"),
            order_id=str(order.get("id") or ""),
        )

    def create_market_buy(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        self._ensure_markets()
        params = self._order_params(symbol, market_kind)
        order = self._call_with_retry(self.client.create_order, symbol, "market", "buy", quantity, None, params)
        trade = self._trade_from_order(symbol, "BUY", quantity, order, "market")
        self.sync([symbol])
        return trade

    def create_market_sell(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        self._ensure_markets()
        params = self._order_params(symbol, market_kind)
        order = self._call_with_retry(self.client.create_order, symbol, "market", "sell", quantity, None, params)
        trade = self._trade_from_order(symbol, "SELL", quantity, order, "market")
        self.sync([symbol])
        return trade

    def create_limit_buy(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        self._ensure_markets()
        params = self._order_params(symbol, market_kind)
        order = self._call_with_retry(self.client.create_order, symbol, "limit", "buy", quantity, price, params)
        created = Order(symbol=symbol, side="BUY", quantity=quantity, price=price, order_type="limit", status=str(order.get("status") or "open"), order_id=str(order.get("id") or ""))
        self.open_orders[created.order_id or f"{symbol}-buy"] = created
        self.sync([symbol])
        return created

    def create_limit_sell(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        self._ensure_markets()
        params = self._order_params(symbol, market_kind)
        order = self._call_with_retry(self.client.create_order, symbol, "limit", "sell", quantity, price, params)
        created = Order(symbol=symbol, side="SELL", quantity=quantity, price=price, order_type="limit", status=str(order.get("status") or "open"), order_id=str(order.get("id") or ""))
        self.open_orders[created.order_id or f"{symbol}-sell"] = created
        self.sync([symbol])
        return created

    def _sync_positions_from_exchange(self, tracked_symbols: Sequence[str]) -> None:
        synced: Dict[str, Position] = {}
        future_symbols = [symbol for symbol in tracked_symbols if self._market_kind_for_symbol(symbol) == "future"]
        if future_symbols and hasattr(self.client, "fetch_positions"):
            try:
                raw_positions = self._fetch_positions_for_symbols(future_symbols)
            except Exception:
                raw_positions = []
            for raw in raw_positions:
                contracts = float(raw.get("contracts") or raw.get("positionAmt") or raw.get("contractsSize") or 0.0)
                if contracts <= 0:
                    continue
                symbol = str(raw.get("symbol") or "")
                entry_price = float(raw.get("entryPrice") or raw.get("entry_price") or raw.get("markPrice") or raw.get("mark_price") or self.fetch_ticker_price(symbol))
                synced[symbol] = Position(
                    symbol=symbol,
                    quantity=contracts,
                    entry_price=entry_price,
                    highest_price=max(entry_price, self.fetch_ticker_price(symbol)),
                    source="exchange",
                )
        balance = self._call_with_retry(self.client.fetch_balance)
        totals = balance.get("total", {})
        for symbol in tracked_symbols:
            if self._market_kind_for_symbol(symbol) != "spot":
                continue
            if "/" not in symbol:
                continue
            base, _quote = symbol.split("/", 1)
            quantity = float(totals.get(base) or 0.0)
            if quantity <= 0:
                continue
            price = self.fetch_ticker_price(symbol)
            previous = self.positions.get(symbol)
            synced[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=previous.entry_price if previous else price,
                stop_loss=previous.stop_loss if previous else None,
                take_profit=previous.take_profit if previous else None,
                highest_price=max(previous.highest_price or price, price) if previous else price,
                trailing_stop_pct=previous.trailing_stop_pct if previous else None,
                source="exchange",
            )
        self.positions = synced

    def _sync_open_orders(self, tracked_symbols: Sequence[str]) -> None:
        if not hasattr(self.client, "fetch_open_orders"):
            self.open_orders = {}
            return
        orders: Dict[str, Order] = {}
        for symbol in tracked_symbols:
            try:
                raw_orders = self._fetch_open_orders_for_symbol(symbol)
            except Exception:
                raw_orders = []
            for raw in raw_orders or []:
                order = Order(
                    symbol=str(raw.get("symbol") or symbol),
                    side=str(raw.get("side") or "").upper(),
                    quantity=float(raw.get("amount") or raw.get("remaining") or 0.0),
                    price=float(raw.get("price") or 0.0),
                    order_type=str(raw.get("type") or "limit"),
                    status=str(raw.get("status") or "open"),
                    order_id=str(raw.get("id") or ""),
                )
                orders[order.order_id or f"{order.symbol}-{order.side}"] = order
        self.open_orders = orders

    def sync(self, tracked_symbols: Sequence[str]) -> None:
        self._ensure_markets()
        self._sync_positions_from_exchange(tracked_symbols)
        self._sync_open_orders(tracked_symbols)

    def fetch_positions(self) -> Sequence[Position]:
        return list(self.positions.values())

    def fetch_open_orders(self) -> Sequence[Order]:
        return list(self.open_orders.values())

    def close_all(self) -> list[Trade]:
        trades: list[Trade] = []
        self.sync(list(self.positions.keys()))
        for symbol, pos in list(self.positions.items()):
            market_kind = self._market_kind_for_symbol(symbol)
            try:
                rule = self.fetch_symbol_rule(symbol)
            except Exception:
                rule = None
            if rule and pos.quantity < rule.min_qty:
                logger.warning(
                    "Skipping close_all for %s: quantity %.12f is below min_qty %.12f",
                    symbol,
                    pos.quantity,
                    rule.min_qty,
                )
                continue
            try:
                trades.append(self.create_market_sell(symbol, pos.quantity, market_kind=market_kind))
            except Exception as exc:
                if self._is_min_amount_error(exc):
                    logger.warning(
                        "Skipping close_all for %s: quantity %.12f rejected by exchange minimum amount rule: %s",
                        symbol,
                        pos.quantity,
                        exc,
                    )
                    continue
                raise
        return trades


class BinanceAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials, retry_attempts: int = 3, retry_delay_seconds: float = 1.0) -> None:
        super().__init__(name="binance", creds=creds, exchange_cls_name="binance", retry_attempts=retry_attempts, retry_delay_seconds=retry_delay_seconds)


class BybitAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials, retry_attempts: int = 3, retry_delay_seconds: float = 1.0) -> None:
        super().__init__(name="bybit", creds=creds, exchange_cls_name="bybit", retry_attempts=retry_attempts, retry_delay_seconds=retry_delay_seconds)


class MexcAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials, retry_attempts: int = 3, retry_delay_seconds: float = 1.0) -> None:
        super().__init__(name="mexc", creds=creds, exchange_cls_name="mexc", retry_attempts=retry_attempts, retry_delay_seconds=retry_delay_seconds)
