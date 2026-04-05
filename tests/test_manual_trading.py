from app.config.settings import load_settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.manual_trading import (
    execute_close_position,
    execute_manual_order,
    parse_manual_order_args,
)
from app.core.models import BotState
from app.core.risk import FixedFractionalRisk
from app.core.state_store import SQLiteStateStore
from app.exchange.paper import PaperExchange
from app.strategy.ma_cross import MovingAverageCrossStrategy


def _build_engine():
    settings = load_settings()
    state = BotState(auto_trading=False, mode="paper", exchange="paper", symbols=["BTC/USDT"], balance_quote=1000)
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    exchange = PaperExchange(balance_quote=1000, prices={"BTC/USDT": 100})
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    engine = TradingEngine(settings, control, exchange, strategy, risk)
    return settings, control, engine, exchange


def test_parse_manual_order_args_for_buy_command() -> None:
    request = parse_manual_order_args(["spot", "BTC/USDT", "0.5", "limit", "99"], side_override="buy")
    assert request.market_kind == "spot"
    assert request.side == "buy"
    assert request.symbol == "BTC/USDT"
    assert request.quantity == 0.5
    assert request.order_type == "limit"
    assert request.price == 99


def test_parse_manual_order_args_with_quote_amount() -> None:
    request = parse_manual_order_args(["spot", "BTC/USDT", "100usdt"], side_override="buy")
    assert request.quantity == 0
    assert request.quote_amount == 100


def test_parse_manual_order_args_with_future_margin_and_leverage() -> None:
    request = parse_manual_order_args(["future", "BTC/USDT", "0.5", "market", "isolated", "10"], side_override="buy")
    assert request.market_kind == "future"
    assert request.margin_mode == "isolated"
    assert request.leverage == 10


def test_parse_manual_order_rejects_future_sell() -> None:
    try:
        parse_manual_order_args(["future", "BTC/USDT:USDT", "1"], side_override="sell")
    except ValueError as exc:
        assert "future sell" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported future sell")


def test_execute_manual_future_buy_normalizes_symbol() -> None:
    settings, control, engine, exchange = _build_engine()
    request = parse_manual_order_args(["future", "BTC/USDT", "1"], side_override="buy")

    message = execute_manual_order(request, settings, control, engine, exchange)

    assert "FUTURE BUY BTC/USDT:USDT" in message
    assert "BTC/USDT:USDT" in control.state.open_positions
    assert "BTC/USDT:USDT" in control.state.symbols
    assert "margin=cross" in message
    assert "lev=1x" in message


def test_execute_manual_market_buy_updates_state() -> None:
    settings, control, engine, exchange = _build_engine()
    request = parse_manual_order_args(["spot", "BTC/USDT", "1"], side_override="buy")

    message = execute_manual_order(request, settings, control, engine, exchange)

    assert "SPOT BUY BTC/USDT" in message
    assert "BTC/USDT" in control.state.open_positions
    assert control.state.balance_quote < 1000


def test_execute_manual_market_buy_with_usdt_amount_updates_state() -> None:
    settings, control, engine, exchange = _build_engine()
    request = parse_manual_order_args(["spot", "BTC/USDT", "100usdt"], side_override="buy")

    message = execute_manual_order(request, settings, control, engine, exchange)

    assert "notional=100.00USDT" in message
    assert control.state.open_positions["BTC/USDT"].quantity == 1


def test_execute_close_position_updates_pnl() -> None:
    settings, control, engine, exchange = _build_engine()
    request = parse_manual_order_args(["spot", "BTC/USDT", "1"], side_override="buy")
    execute_manual_order(request, settings, control, engine, exchange)
    exchange.set_price("BTC/USDT", 110)

    message = execute_close_position("spot", "BTC/USDT", settings, control, engine, exchange)

    assert "SPOT CLOSE BTC/USDT" in message
    assert "BTC/USDT" not in control.state.open_positions
    assert control.state.daily_pnl > 0
