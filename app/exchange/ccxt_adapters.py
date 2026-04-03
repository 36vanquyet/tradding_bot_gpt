from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence

try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover
    ccxt = None

from app.config.settings import ExchangeCredentials
from app.core.models import Position, SymbolRule, Trade
from app.exchange.base import ExchangeAdapter


@dataclass
class CCXTAdapter(ExchangeAdapter):
    name: str
    creds: ExchangeCredentials
    exchange_cls_name: str

    def __post_init__(self) -> None:
        if ccxt is None:
            raise RuntimeError("ccxt is not installed")
        cls = getattr(ccxt, self.exchange_cls_name)
        self.client = cls(
            {
                "apiKey": self.creds.api_key,
                "secret": self.creds.api_secret,
                "enableRateLimit": True,
            }
        )
        if self.creds.testnet and hasattr(self.client, "set_sandbox_mode"):
            self.client.set_sandbox_mode(True)
        self._markets_loaded = False
        self.positions: Dict[str, Position] = {}

    def _ensure_markets(self) -> None:
        if not self._markets_loaded:
            self.client.load_markets()
            self._markets_loaded = True

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list[list[float]]:
        self._ensure_markets()
        return self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_balance_quote(self, quote: str = "USDT") -> float:
        self._ensure_markets()
        balance = self.client.fetch_balance()
        free_bal = balance.get("free", {})
        return float(free_bal.get(quote, 0.0))

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
        ticker = self.client.fetch_ticker(symbol)
        return float(ticker.get("last") or ticker.get("close") or 0.0)

    def create_market_buy(self, symbol: str, quantity: float) -> Trade:
        self._ensure_markets()
        order = self.client.create_market_buy_order(symbol, quantity)
        avg_price = float(order.get("average") or order.get("price") or self.fetch_ticker_price(symbol))
        fee_cost = 0.0
        fees = order.get("fees") or []
        if fees:
            fee_cost = sum(float(x.get("cost") or 0.0) for x in fees)
        elif order.get("fee"):
            fee_cost = float((order.get("fee") or {}).get("cost") or 0.0)
        self.positions[symbol] = Position(symbol=symbol, quantity=quantity, entry_price=avg_price)
        return Trade(symbol=symbol, side="BUY", quantity=quantity, price=avg_price, fee=fee_cost, mode="live")

    def create_market_sell(self, symbol: str, quantity: float) -> Trade:
        self._ensure_markets()
        order = self.client.create_market_sell_order(symbol, quantity)
        avg_price = float(order.get("average") or order.get("price") or self.fetch_ticker_price(symbol))
        fee_cost = 0.0
        fees = order.get("fees") or []
        if fees:
            fee_cost = sum(float(x.get("cost") or 0.0) for x in fees)
        elif order.get("fee"):
            fee_cost = float((order.get("fee") or {}).get("cost") or 0.0)
        self.positions.pop(symbol, None)
        return Trade(symbol=symbol, side="SELL", quantity=quantity, price=avg_price, fee=fee_cost, mode="live")

    def fetch_positions(self) -> Sequence[Position]:
        return list(self.positions.values())

    def close_all(self) -> list[Trade]:
        trades: list[Trade] = []
        for symbol, pos in list(self.positions.items()):
            trades.append(self.create_market_sell(symbol, pos.quantity))
        return trades


class BinanceAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials) -> None:
        super().__init__(name="binance", creds=creds, exchange_cls_name="binance")


class BybitAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials) -> None:
        super().__init__(name="bybit", creds=creds, exchange_cls_name="bybit")


class MexcAdapter(CCXTAdapter):
    def __init__(self, creds: ExchangeCredentials) -> None:
        super().__init__(name="mexc", creds=creds, exchange_cls_name="mexc")
