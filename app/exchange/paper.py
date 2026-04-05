from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from app.core.models import Order, Position, SymbolRule, Trade
from app.exchange.base import ExchangeAdapter


@dataclass
class PaperExchange(ExchangeAdapter):
    name: str = "paper"
    balance_quote: float = 10000.0
    fee_rate: float = 0.001
    prices: Dict[str, float] = field(default_factory=lambda: {"BTC/USDT": 50000.0})
    positions: Dict[str, Position] = field(default_factory=dict)
    open_orders: Dict[str, Order] = field(default_factory=dict)
    default_stop_loss_pct: float = 0.02
    default_take_profit_pct: float = 0.04
    default_trailing_stop_pct: float = 0.01
    rules: Dict[str, SymbolRule] = field(default_factory=lambda: {
        "BTC/USDT": SymbolRule(min_qty=0.0001, step_size=0.0001, min_notional=5.0),
        "ETH/USDT": SymbolRule(min_qty=0.001, step_size=0.001, min_notional=5.0),
    })

    def _next_order_id(self) -> str:
        return f"paper-{len(self.open_orders) + len(self.positions) + 1}"

    def _build_position(self, symbol: str, quantity: float, price: float, source: str = "paper") -> Position:
        stop_loss = price * (1 - self.default_stop_loss_pct)
        take_profit = price * (1 + self.default_take_profit_pct)
        return Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            highest_price=price,
            trailing_stop_pct=self.default_trailing_stop_pct,
            source=source,
        )

    def _fill_limit_orders(self) -> None:
        for order_id, order in list(self.open_orders.items()):
            current_price = self.fetch_ticker_price(order.symbol)
            should_fill = (
                order.side == "BUY" and current_price <= order.price
            ) or (
                order.side == "SELL" and current_price >= order.price
            )
            if not should_fill:
                continue
            if order.side == "BUY":
                self._execute_buy(order.symbol, order.quantity, order.price, order_type="limit")
            else:
                self._execute_sell(order.symbol, order.quantity, order.price, order_type="limit")
            self.open_orders.pop(order_id, None)

    def set_price(self, symbol: str, price: float) -> None:
        self.prices[symbol] = price
        self._fill_limit_orders()

    def sync(self, tracked_symbols: Sequence[str]) -> None:
        for symbol in tracked_symbols:
            self.prices.setdefault(symbol, self.prices.get(symbol, 100.0))
        self._fill_limit_orders()

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[float]]:
        price = self.prices.get(symbol, 100.0)
        return [[i, price, price, price, price, 1.0] for i in range(limit)]

    def fetch_balance_quote(self, quote: str = "USDT", market_kind: str = "spot") -> float:
        return self.balance_quote

    def fetch_symbol_rule(self, symbol: str) -> SymbolRule:
        return self.rules.get(symbol, SymbolRule())

    def fetch_ticker_price(self, symbol: str) -> float:
        return float(self.prices.get(symbol, 0.0))

    def _execute_buy(self, symbol: str, quantity: float, price: float, order_type: str = "market") -> Trade:
        cost = price * quantity
        fee = cost * self.fee_rate
        total = cost + fee
        if total > self.balance_quote:
            raise ValueError("Insufficient paper balance")
        self.balance_quote -= total
        self.positions[symbol] = self._build_position(symbol, quantity, price)
        return Trade(symbol=symbol, side="BUY", quantity=quantity, price=price, fee=fee, mode="paper", order_type=order_type)

    def _execute_sell(self, symbol: str, quantity: float, price: float, order_type: str = "market") -> Trade:
        if symbol not in self.positions:
            raise ValueError("No paper position to close")
        pos = self.positions[symbol]
        if quantity > pos.quantity:
            raise ValueError("Quantity larger than paper position")
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
                highest_price=pos.highest_price,
                trailing_stop_pct=pos.trailing_stop_pct,
                source=pos.source,
            )
        return Trade(symbol=symbol, side="SELL", quantity=quantity, price=price, fee=fee, mode="paper", order_type=order_type)

    def create_market_buy(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        return self._execute_buy(symbol, quantity, self.fetch_ticker_price(symbol), order_type="market")

    def create_market_sell(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        return self._execute_sell(symbol, quantity, self.fetch_ticker_price(symbol), order_type="market")

    def create_limit_buy(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        order = Order(symbol=symbol, side="BUY", quantity=quantity, price=price, order_type="limit", status="open", order_id=self._next_order_id())
        self.open_orders[order.order_id] = order
        self._fill_limit_orders()
        return order

    def create_limit_sell(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        order = Order(symbol=symbol, side="SELL", quantity=quantity, price=price, order_type="limit", status="open", order_id=self._next_order_id())
        self.open_orders[order.order_id] = order
        self._fill_limit_orders()
        return order

    def fetch_positions(self) -> Sequence[Position]:
        return list(self.positions.values())

    def fetch_open_orders(self) -> Sequence[Order]:
        return list(self.open_orders.values())

    def close_all(self) -> list[Trade]:
        trades: list[Trade] = []
        for symbol, pos in list(self.positions.items()):
            trades.append(self.create_market_sell(symbol, pos.quantity))
        self.open_orders.clear()
        return trades
