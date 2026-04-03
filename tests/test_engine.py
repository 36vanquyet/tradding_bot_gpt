from app.config.settings import load_settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.models import BotState
from app.core.risk import FixedFractionalRisk
from app.core.state_store import SQLiteStateStore
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
