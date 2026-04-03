from __future__ import annotations

import math

from app.core.models import SymbolRule


class FixedFractionalRisk:
    def __init__(self, risk_per_trade: float) -> None:
        if risk_per_trade <= 0:
            raise ValueError("risk_per_trade must be > 0")
        self.risk_per_trade = risk_per_trade

    def quantity_from_balance(self, balance_quote: float, price: float) -> float:
        if price <= 0:
            return 0.0
        return (balance_quote * self.risk_per_trade) / price

    def normalize_quantity(self, qty: float, rule: SymbolRule) -> float:
        if qty <= 0:
            return 0.0
        steps = math.floor(qty / rule.step_size)
        normalized = steps * rule.step_size
        if normalized < rule.min_qty:
            return 0.0
        return round(normalized, 10)

    def sized_quantity(self, balance_quote: float, price: float, rule: SymbolRule) -> float:
        raw_qty = self.quantity_from_balance(balance_quote, price)
        qty = self.normalize_quantity(raw_qty, rule)
        if qty * price < rule.min_notional:
            return 0.0
        return qty
