from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import Settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.models import Order, Trade
from app.exchange.base import ExchangeAdapter


@dataclass(frozen=True)
class ManualOrderRequest:
    market_kind: str
    side: str
    symbol: str
    quantity: float
    quote_amount: float | None = None
    order_type: str = "market"
    price: float | None = None
    margin_mode: str | None = None
    leverage: float | None = None


def parse_manual_order_args(args: list[str], side_override: str | None = None) -> ManualOrderRequest:
    if side_override is None:
        if len(args) < 4:
            raise ValueError("Usage: /order <spot|future> <buy|sell> <symbol> <quantity> [market|limit] [price]")
        market_kind = args[0].lower()
        side = args[1].lower()
        symbol = args[2].upper()
        quantity_arg = args[3]
        tail = args[4:]
    else:
        if len(args) < 3:
            raise ValueError(f"Usage: /{side_override.lower()} <spot|future> <symbol> <quantity> [market|limit] [price]")
        market_kind = args[0].lower()
        side = side_override.lower()
        symbol = args[1].upper()
        quantity_arg = args[2]
        tail = args[3:]

    if market_kind not in {"spot", "future"}:
        raise ValueError("market_kind must be 'spot' or 'future'")
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    quantity, quote_amount = _parse_quantity_arg(quantity_arg, side)

    order_type = "market"
    price: float | None = None
    margin_mode: str | None = None
    leverage: float | None = None
    if tail:
        order_type = tail[0].lower()
        if order_type not in {"market", "limit"}:
            raise ValueError("order_type must be 'market' or 'limit'")
        if order_type == "limit":
            if len(tail) < 2:
                raise ValueError("limit order requires a price")
            price = float(tail[1])
            if price <= 0:
                raise ValueError("price must be > 0")
            tail = tail[2:]
        else:
            tail = tail[1:]

    if market_kind == "future" and tail:
        margin_mode = tail[0].lower()
        if margin_mode not in {"cross", "isolated"}:
            raise ValueError("margin_mode must be 'cross' or 'isolated'")
        if len(tail) > 1:
            leverage = float(tail[1])
            if leverage <= 0:
                raise ValueError("leverage must be > 0")

    if market_kind == "future" and side == "sell":
        raise ValueError("future sell is not supported yet; use /close to reduce an existing long")

    return ManualOrderRequest(
        market_kind=market_kind,
        side=side,
        symbol=symbol,
        quantity=quantity,
        quote_amount=quote_amount,
        order_type=order_type,
        price=price,
        margin_mode=margin_mode,
        leverage=leverage,
    )


def execute_manual_order(
    request: ManualOrderRequest,
    settings: Settings,
    control: ControlService,
    engine: TradingEngine,
    exchange: ExchangeAdapter,
) -> str:
    symbol = _normalize_symbol_for_market(request.symbol, request.market_kind)
    if symbol not in control.state.symbols:
        control.add_symbol(symbol)
    normalized = ManualOrderRequest(
        market_kind=request.market_kind,
        side=request.side,
        symbol=symbol,
        quantity=_resolve_order_quantity(request, exchange),
        quote_amount=request.quote_amount,
        order_type=request.order_type,
        price=request.price,
        margin_mode=request.margin_mode or (settings.future_margin_mode if request.market_kind == "future" else None),
        leverage=request.leverage or (settings.future_leverage if request.market_kind == "future" else None),
    )
    if normalized.market_kind == "future":
        exchange.configure_futures(normalized.symbol, normalized.margin_mode, normalized.leverage)
    result = _submit_order(normalized, exchange)
    engine.sync_positions_into_state()
    control.state.balance_quote = exchange.fetch_balance_quote(settings.quote_asset, market_kind=normalized.market_kind)

    scope = normalized.market_kind.upper()
    if isinstance(result, Order):
        message = (
            f"{scope} LIMIT {result.side} {result.symbol} "
            f"qty={result.quantity:.6f} @ {result.price:.2f} status={result.status}"
        )
    else:
        message = (
            f"{scope} {result.side} {result.symbol} "
            f"qty={result.quantity:.6f} @ {result.price:.2f} "
            f"type={result.order_type} fee={result.fee:.6f}"
        )
    if normalized.quote_amount is not None:
        message += f" notional={normalized.quote_amount:.2f}USDT"
    if normalized.market_kind == "future":
        if normalized.margin_mode:
            message += f" margin={normalized.margin_mode}"
        if normalized.leverage:
            message += f" lev={normalized.leverage:g}x"

    control.state.last_trade = message
    control.persist_engine_state()
    return message


def execute_close_position(
    market_kind: str,
    symbol: str,
    settings: Settings,
    control: ControlService,
    engine: TradingEngine,
    exchange: ExchangeAdapter,
    quantity: float | None = None,
) -> str:
    market_kind = market_kind.lower()
    if market_kind not in {"spot", "future"}:
        raise ValueError("market_kind must be 'spot' or 'future'")
    symbol = _normalize_symbol_for_market(symbol.upper(), market_kind)
    if symbol not in control.state.symbols:
        control.add_symbol(symbol)
    engine.sync_positions_into_state()
    if symbol not in control.state.open_positions:
        raise ValueError(f"No open position for {symbol}")
    position = control.state.open_positions[symbol]
    close_qty = quantity if quantity is not None else position.quantity
    if close_qty <= 0:
        raise ValueError("quantity must be > 0")
    if close_qty > position.quantity:
        raise ValueError("quantity exceeds current position")

    trade = exchange.create_market_sell(symbol, close_qty, market_kind=market_kind)
    pnl = (trade.price - position.entry_price) * close_qty - trade.fee
    control.state.daily_pnl += pnl
    engine.sync_positions_into_state()
    control.state.balance_quote = exchange.fetch_balance_quote(settings.quote_asset, market_kind=market_kind)
    message = (
        f"{market_kind.upper()} CLOSE {trade.symbol} qty={trade.quantity:.6f} "
        f"@ {trade.price:.2f} pnl={pnl:.2f}"
    )
    control.state.last_trade = message
    control.persist_engine_state()
    return message


def _submit_order(request: ManualOrderRequest, exchange: ExchangeAdapter) -> Trade | Order:
    if request.order_type == "limit":
        if request.price is None:
            raise ValueError("limit order requires a price")
        if request.side == "buy":
            return exchange.create_limit_buy(request.symbol, request.quantity, request.price, market_kind=request.market_kind)
        return exchange.create_limit_sell(request.symbol, request.quantity, request.price, market_kind=request.market_kind)

    if request.side == "buy":
        return exchange.create_market_buy(request.symbol, request.quantity, market_kind=request.market_kind)
    return exchange.create_market_sell(request.symbol, request.quantity, market_kind=request.market_kind)


def _normalize_symbol_for_market(symbol: str, market_kind: str) -> str:
    if market_kind != "future" or ":" in symbol or "/" not in symbol:
        return symbol
    base, quote = symbol.split("/", 1)
    return f"{base}/{quote}:{quote}"


def _parse_quantity_arg(quantity_arg: str, side: str) -> tuple[float, float | None]:
    raw = quantity_arg.strip().lower()
    if raw.endswith("usdt") or raw.endswith("usd"):
        if side != "buy":
            raise ValueError("quote amount like '100usdt' is only supported for buy orders")
        suffix_len = 4 if raw.endswith("usdt") else 3
        quote_amount = float(raw[:-suffix_len])
        if quote_amount <= 0:
            raise ValueError("quote amount must be > 0")
        return 0.0, quote_amount
    quantity = float(quantity_arg)
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    return quantity, None


def _resolve_order_quantity(request: ManualOrderRequest, exchange: ExchangeAdapter) -> float:
    if request.quote_amount is None:
        return request.quantity
    price = request.price if request.order_type == "limit" and request.price is not None else exchange.fetch_ticker_price(request.symbol)
    if price <= 0:
        raise ValueError("unable to resolve symbol price for quote amount order")
    quantity = request.quote_amount / price
    if quantity <= 0:
        raise ValueError("resolved quantity must be > 0")
    return quantity
