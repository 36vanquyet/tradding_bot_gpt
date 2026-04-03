from app.config.settings import load_settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.models import BotState
from app.core.risk import FixedFractionalRisk
from app.core.state_store import SQLiteStateStore
from app.exchange.paper import PaperExchange
from app.strategy.ma_cross import MovingAverageCrossStrategy


def main() -> None:
    settings = load_settings()
    store = SQLiteStateStore(":memory:")
    state = BotState(auto_trading=True, mode="paper", exchange="paper", symbols=["BTC/USDT"], balance_quote=10000)
    control = ControlService(state, store)
    exchange = PaperExchange(balance_quote=10000, prices={"BTC/USDT": 100.0}, default_stop_loss_pct=0.02, default_take_profit_pct=0.04)
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    engine = TradingEngine(settings, control, exchange, strategy, risk)

    exchange.fetch_ohlcv = lambda symbol, timeframe, limit=100: [[i, 0, 0, 0, p, 1] for i, p in enumerate(list(range(1, 200)))]
    engine.run_n_steps_sync(1)
    exchange.set_price("BTC/USDT", 106.0)
    exchange.fetch_ohlcv = lambda symbol, timeframe, limit=100: [[i, 0, 0, 0, p, 1] for i, p in enumerate(list(range(200, 1, -1)))]
    engine.run_n_steps_sync(1)

    print("Sample finished")
    print(control.get_status())


if __name__ == "__main__":
    main()
