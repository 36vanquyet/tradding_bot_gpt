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
