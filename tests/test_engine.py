from app.config.settings import load_settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.models import BotState, Order, Position, SymbolRule
from app.core.risk import FixedFractionalRisk
from app.core.state_store import SQLiteStateStore
from app.exchange.base import ExchangeAdapter
from app.exchange.paper import PaperExchange
from app.strategy.ma_cross import MovingAverageCrossStrategy


def test_engine_updates_heartbeat() -> None:
    settings = load_settings()
    state = BotState(auto_trading=False, mode="paper", exchange="paper", symbols=["BTC/USDT"])
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    exchange = PaperExchange(balance_quote=1000, prices={"BTC/USDT": 100})
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    engine = TradingEngine(settings, control, exchange, strategy, risk)
    engine.run_n_steps_sync(1)
    assert control.get_status()["heartbeat_ts"] > 0


def test_engine_stop_loss_take_profit() -> None:
    settings = load_settings()
    state = BotState(auto_trading=False, mode="paper", exchange="paper", symbols=["BTC/USDT"], balance_quote=1000)
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    exchange = PaperExchange(balance_quote=1000, prices={"BTC/USDT": 100}, default_stop_loss_pct=0.02, default_take_profit_pct=0.04)
    exchange.create_market_buy("BTC/USDT", 1)
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    engine = TradingEngine(settings, control, exchange, strategy, risk)
    engine.sync_positions_into_state()
    exchange.set_price("BTC/USDT", 104.0)
    engine.run_n_steps_sync(1)
    assert "BTC/USDT" not in control.state.open_positions


def test_engine_trailing_stop_moves_up() -> None:
    settings = load_settings()
    state = BotState(auto_trading=False, mode="paper", exchange="paper", symbols=["BTC/USDT"], balance_quote=1000)
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    exchange = PaperExchange(
        balance_quote=1000,
        prices={"BTC/USDT": 100},
        default_stop_loss_pct=0.02,
        default_take_profit_pct=0.5,
        default_trailing_stop_pct=0.01,
    )
    exchange.create_market_buy("BTC/USDT", 1)
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    engine = TradingEngine(settings, control, exchange, strategy, risk)
    engine.sync_positions_into_state()

    old_stop = control.state.open_positions["BTC/USDT"].stop_loss
    exchange.set_price("BTC/USDT", 110.0)
    engine.run_n_steps_sync(1)

    assert control.state.open_positions["BTC/USDT"].stop_loss > old_stop


class _NotifierStub:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str) -> None:
        self.messages.append(message)


class _DustExchange(ExchangeAdapter):
    name = "dust"

    def __init__(self) -> None:
        self.positions = {
            "ETH/USDT": Position(
                symbol="ETH/USDT",
                quantity=0.000001,
                entry_price=100.0,
                stop_loss=99.0,
                take_profit=120.0,
                highest_price=100.0,
                source="exchange",
            )
        }

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list[list[float]]:
        return [[i, 100.0, 100.0, 100.0, 100.0, 1.0] for i in range(limit)]

    def fetch_balance_quote(self, quote: str = "USDT", market_kind: str = "spot") -> float:
        return 1000.0

    def create_market_buy(self, symbol: str, quantity: float, market_kind: str = "spot"):
        raise NotImplementedError

    def create_market_sell(self, symbol: str, quantity: float, market_kind: str = "spot"):
        raise AssertionError("dust position should be skipped before create_market_sell")

    def create_limit_buy(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        raise NotImplementedError

    def create_limit_sell(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        raise NotImplementedError

    def fetch_positions(self):
        return list(self.positions.values())

    def fetch_open_orders(self):
        return []

    def sync(self, tracked_symbols):
        return None

    def close_all(self):
        return []

    def fetch_symbol_rule(self, symbol: str) -> SymbolRule:
        return SymbolRule(min_qty=0.01, step_size=0.01, min_notional=5.0)

    def fetch_ticker_price(self, symbol: str) -> float:
        return 90.0


def test_engine_skips_dust_close_only_once() -> None:
    settings = load_settings()
    state = BotState(auto_trading=False, mode="live", exchange="bybit", symbols=["ETH/USDT"], balance_quote=1000)
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    exchange = _DustExchange()
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    notifier = _NotifierStub()
    engine = TradingEngine(settings, control, exchange, strategy, risk, notifier=notifier)

    engine.run_n_steps_sync(1)
    engine.run_n_steps_sync(1)

    assert notifier.messages == ["SKIP CLOSE ETH/USDT qty=0.000001 below min_qty=0.010000"]
