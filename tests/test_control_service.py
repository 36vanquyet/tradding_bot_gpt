from app.core.control_service import ControlService
from app.core.models import BotState, Order
from app.core.state_store import SQLiteStateStore


def test_control_toggle() -> None:
    state = BotState()
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)
    control.enable_auto()
    assert control.get_status()["auto_trading"] is True
    control.pause_bot()
    assert control.get_status()["bot_running"] is False
    control.add_symbol("ETH/USDT")
    assert "ETH/USDT" in control.state.symbols


def test_control_language_persisted() -> None:
    default_state = BotState()
    store = SQLiteStateStore(":memory:")
    control = ControlService(default_state, store)
    control.set_language("en")

    loaded = store.load_state(BotState())
    assert loaded.language == "en"
    assert control.get_status()["language"] == "en"


def test_state_store_persists_pending_orders() -> None:
    state = BotState(pending_orders={"o1": Order(symbol="BTC/USDT", side="BUY", quantity=1, price=99, order_id="o1")})
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)

    loaded = store.load_state(BotState())
    assert "o1" in loaded.pending_orders
    assert loaded.pending_orders["o1"].price == 99


def test_runtime_config_persisted_across_restart() -> None:
    initial = BotState(
        mode="paper",
        exchange="binance",
        language="vi",
        symbols=["BTC/USDT"],
        default_mode="paper",
        default_exchange="binance",
        default_language="vi",
        default_symbols=["BTC/USDT"],
    )
    store = SQLiteStateStore(":memory:")
    control = ControlService(initial, store)
    control.set_mode("live")
    control.set_exchange("mexc")
    control.set_language("en")
    control.set_symbols(["ETH/USDT", "BTC/USDT"])
    control.enable_auto()
    control.pause_bot()

    loaded = store.load_state(initial)
    assert loaded.mode == "live"
    assert loaded.exchange == "mexc"
    assert loaded.language == "en"
    assert loaded.symbols == ["ETH/USDT", "BTC/USDT"]
    assert loaded.auto_trading is True
    assert loaded.bot_running is False


def test_reset_runtime_config_restores_defaults() -> None:
    state = BotState(
        bot_running=False,
        auto_trading=True,
        mode="live",
        exchange="mexc",
        language="en",
        symbols=["ETH/USDT"],
        default_bot_running=True,
        default_auto_trading=False,
        default_mode="paper",
        default_exchange="binance",
        default_language="vi",
        default_symbols=["BTC/USDT", "ETH/USDT"],
    )
    store = SQLiteStateStore(":memory:")
    control = ControlService(state, store)

    control.reset_runtime_config()

    assert control.state.bot_running is True
    assert control.state.auto_trading is False
    assert control.state.mode == "paper"
    assert control.state.exchange == "binance"
    assert control.state.language == "vi"
    assert control.state.symbols == ["BTC/USDT", "ETH/USDT"]


def test_state_store_uses_same_file_across_cwd_changes(tmp_path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    db_path = project_dir / "bot_state.db"

    first_store = SQLiteStateStore(str(db_path))
    first_control = ControlService(BotState(mode="live", exchange="mexc", language="en"), first_store)

    loaded = SQLiteStateStore(str(db_path)).load_state(BotState())
    assert loaded.mode == "live"
    assert loaded.exchange == "mexc"
    assert loaded.language == "en"
