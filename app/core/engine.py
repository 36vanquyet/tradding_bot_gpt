from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from app.config.settings import Settings
from app.core.control_service import ControlService
from app.core.models import Order, Position
from app.core.risk import FixedFractionalRisk
from app.exchange.base import ExchangeAdapter
from app.strategy.ma_cross import MovingAverageCrossStrategy
from app.telegram.notifier import TelegramNotifier

logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(
        self,
        settings: Settings,
        control: ControlService,
        exchange: ExchangeAdapter,
        strategy: MovingAverageCrossStrategy,
        risk: FixedFractionalRisk,
        notifier: Optional[TelegramNotifier] = None,
    ) -> None:
        self.settings = settings
        self.control = control
        self.exchange = exchange
        self.strategy = strategy
        self.risk = risk
        self.notifier = notifier or TelegramNotifier()
        self._stop = False

    def set_exchange(self, exchange: ExchangeAdapter) -> None:
        self.exchange = exchange

    def stop(self) -> None:
        self._stop = True

    def sync_positions_into_state(self) -> None:
        self.exchange.sync(self.control.state.symbols)
        positions = self.exchange.fetch_positions()
        self.control.state.open_positions = {
            pos.symbol: Position(
                symbol=pos.symbol,
                quantity=pos.quantity,
                entry_price=pos.entry_price,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                highest_price=pos.highest_price,
                trailing_stop_pct=pos.trailing_stop_pct,
                source=pos.source,
            )
            for pos in positions
        }
        self.control.state.pending_orders = {
            order.order_id or f"{order.symbol}-{order.side}": Order(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=order.price,
                order_type=order.order_type,
                status=order.status,
                order_id=order.order_id,
            )
            for order in self.exchange.fetch_open_orders()
        }
        self.control.persist_engine_state()

    async def notify(self, message: str) -> None:
        await self.notifier.send(message)

    def _apply_trailing_stop(self, pos: Position, current_price: float) -> bool:
        trailing_pct = pos.trailing_stop_pct or self.settings.trailing_stop_pct
        updated = False
        highest_price = pos.highest_price or pos.entry_price
        if current_price > highest_price:
            highest_price = current_price
            pos.highest_price = current_price
            updated = True
        if trailing_pct > 0:
            trailing_stop = highest_price * (1 - trailing_pct)
            if pos.stop_loss is None or trailing_stop > pos.stop_loss:
                pos.stop_loss = trailing_stop
                updated = True
        if updated and hasattr(self.exchange, "positions") and pos.symbol in getattr(self.exchange, "positions", {}):
            self.exchange.positions[pos.symbol].highest_price = pos.highest_price
            self.exchange.positions[pos.symbol].stop_loss = pos.stop_loss
            self.exchange.positions[pos.symbol].trailing_stop_pct = trailing_pct
        return updated

    def _protect_positions(self) -> list[str]:
        alerts: list[str] = []
        changed = False
        for symbol, pos in list(self.control.state.open_positions.items()):
            current_price = self.exchange.fetch_ticker_price(symbol)
            if self._apply_trailing_stop(pos, current_price):
                changed = True
            if pos.stop_loss is not None and current_price <= pos.stop_loss:
                trade = self.exchange.create_market_sell(symbol, pos.quantity)
                pnl = (trade.price - pos.entry_price) * pos.quantity - trade.fee
                self.control.state.daily_pnl += pnl
                alerts.append(f"STOP LOSS {symbol} qty={trade.quantity:.6f} @ {trade.price:.2f} pnl={pnl:.2f}")
            elif pos.take_profit is not None and current_price >= pos.take_profit:
                trade = self.exchange.create_market_sell(symbol, pos.quantity)
                pnl = (trade.price - pos.entry_price) * pos.quantity - trade.fee
                self.control.state.daily_pnl += pnl
                alerts.append(f"TAKE PROFIT {symbol} qty={trade.quantity:.6f} @ {trade.price:.2f} pnl={pnl:.2f}")
        if alerts or changed:
            self.sync_positions_into_state()
            self.control.state.balance_quote = self.exchange.fetch_balance_quote(self.settings.quote_asset)
            self.control.persist_engine_state()
        return alerts

    def _entry_limit_price(self, price: float) -> float:
        return price * (1 - self.settings.limit_price_offset_pct)

    async def _place_entry(self, symbol: str, quantity: float, price: float) -> None:
        if self.settings.entry_order_type == "limit":
            limit_price = self._entry_limit_price(price)
            order = self.exchange.create_limit_buy(symbol, quantity, limit_price)
            self.control.state.last_trade = f"LIMIT BUY {order.symbol} qty={order.quantity:.6f} @ {order.price:.2f} status={order.status}"
        else:
            trade = self.exchange.create_market_buy(symbol, quantity)
            position = self.exchange.positions.get(symbol) if hasattr(self.exchange, "positions") else None
            self.control.state.last_trade = (
                f"BUY {trade.symbol} qty={trade.quantity:.6f} @ {trade.price:.2f} "
                f"sl={position.stop_loss if position else None} tp={position.take_profit if position else None}"
            )
        await self.notify(self.control.state.last_trade)

    async def step(self) -> None:
        try:
            status = self.control.get_status()
            if not status["bot_running"]:
                return
            self.control.set_heartbeat()
            self.sync_positions_into_state()
            self.control.state.balance_quote = self.exchange.fetch_balance_quote(self.settings.quote_asset)
            self.control.persist_engine_state()

            for msg in self._protect_positions():
                self.control.state.last_trade = msg
                await self.notify(msg)

            if not status["auto_trading"]:
                return

            if len(self.control.state.open_positions) >= self.settings.max_open_positions:
                return

            for symbol in status["symbols"]:
                candles = self.exchange.fetch_ohlcv(symbol, self.settings.default_timeframe, limit=200)
                closes = [float(c[4]) for c in candles]
                signal = self.strategy.generate_signal(closes)
                self.control.state.last_signal = f"{symbol}: {signal}"
                if signal == "BUY" and symbol not in self.control.state.open_positions:
                    price = closes[-1]
                    rule = self.exchange.fetch_symbol_rule(symbol)
                    quantity = self.risk.sized_quantity(self.control.state.balance_quote, price, rule)
                    if quantity > 0:
                        await self._place_entry(symbol, quantity, price)
                elif signal == "SELL" and symbol in self.control.state.open_positions:
                    pos = self.control.state.open_positions[symbol]
                    trade = self.exchange.create_market_sell(symbol, pos.quantity)
                    pnl = (trade.price - pos.entry_price) * pos.quantity - trade.fee
                    self.control.state.daily_pnl += pnl
                    self.control.state.last_trade = f"SELL {trade.symbol} qty={trade.quantity:.6f} @ {trade.price:.2f} pnl={pnl:.2f}"
                    await self.notify(self.control.state.last_trade)
                self.sync_positions_into_state()
                self.control.state.balance_quote = self.exchange.fetch_balance_quote(self.settings.quote_asset)
                self.control.persist_engine_state()
        except Exception as exc:  # pragma: no cover
            logger.exception("Engine step failed")
            self.control.set_error(str(exc))
            await self.notify(f"ERROR: {exc}")

    async def run_forever(self) -> None:
        while not self._stop:
            await self.step()
            await asyncio.sleep(self.settings.poll_interval_seconds)

    def run_n_steps_sync(self, steps: int = 1) -> None:
        for _ in range(steps):
            asyncio.run(self.step())
            time.sleep(0.01)
