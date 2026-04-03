from app.core.models import SymbolRule
from app.core.risk import FixedFractionalRisk


def test_quantity_from_balance() -> None:
    risk = FixedFractionalRisk(0.01)
    qty = risk.sized_quantity(10000, 100, SymbolRule(min_qty=0.1, step_size=0.1, min_notional=5))
    assert round(qty, 4) == 1.0
