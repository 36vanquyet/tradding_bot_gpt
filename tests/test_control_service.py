from app.core.control_service import ControlService
from app.core.models import BotState
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
