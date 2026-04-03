from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from app.core.models import Position, SymbolRule, Trade
from app.exchange.base import ExchangeAdapter


@dataclass
class PaperExchange(ExchangeAdapter):
    name: str = "paper"
    balance_quote: float = 10000.0
    fee_rate: float = 0.001
    prices: Dict[str, float] = field(default_factory=lambda: {"BTC/USDT": 50000.0})
    positions: Dict[str, Position] = field(default_factory=dict)
    default_stop_loss_pct: float = 0.02
    default_take_profit_pct: float = 0.04
    rules: Dict[str, SymbolRule] = field(default_factory=lambda: {
        "BTC/USDT": SymbolRule(min_qty=0.0001, step_size=0.0001, min_notional=5.0),
        "ETH/USDT": SymbolRule(min_qty=0.001, step_size=0.001, min_notional=5.0),
    })

    def set_price(self, symbol: str, price: float) -> None:
        self.prices[symbol] = price

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[float]]:
        price = self.prices.get(symbol, 100.0)
        return [[i, price, price, price, price, 1.0] for i in range(limit)]

    def fetch_balance_quote(self, quote: str = "USDT") -> float:
        return self.balance_quote

    def fetch_symbol_rule(self, symbol: str) -> SymbolRule:
        return self.rules.get(symbol, SymbolRule())

    def fetch_ticker_price(self, symbol: str) -> float:
        return float(self.prices.get(symbol, 0.0))

    def create_market_buy(self, symbol: str, quantity: float) -> Trade:
        price = self.fetch_ticker_price(symbol)
        cost = price * quantity
        fee = cost * self.fee_rate
        total = cost + fee
        if total > self.balance_quote:
            raise ValueError("Insufficient paper balance")
        self.balance_quote -= total
        stop_loss = price * (1 - self.default_stop_loss_pct)
        take_profit = price * (1 + self.default_take_profit_pct)
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return Trade(symbol=symbol, side="BUY", quantity=quantity, price=price, fee=fee, mode="paper")

    def create_market_sell(self, symbol: str, quantity: float) -> Trade:
        if symbol not in self.positions:
            raise ValueError("No paper position to close")
        pos = self.positions[symbol]
        if quantity > pos.quantity:
            raise ValueError("Quantity larger than paper position")
        price = self.fetch_ticker_price(symbol)
        proceeds = price * quantity
        fee = proceeds * self.fee_rate
        self.balance_quote += proceeds - fee
        remaining = round(pos.quantity - quantity, 10)
        if remaining <= 0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=remaining,
                entry_price=pos.entry_price,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
            )
        return Trade(symbol=symbol, side="SELL", quantity=quantity, price=price, fee=fee, mode="paper")

    def fetch_positions(self) -> Sequence[Position]:
        return list(self.positions.values())

    def close_all(self) -> list[Trade]:
        trades: list[Trade] = []
        for symbol, pos in list(self.positions.items()):
            trades.append(self.create_market_sell(symbol, pos.quantity))
        return trades
