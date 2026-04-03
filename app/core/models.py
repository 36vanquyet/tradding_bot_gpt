from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    highest_price: float | None = None
    trailing_stop_pct: float | None = None
    source: str = "local"


@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float = 0.0
    mode: str = "paper"
    order_type: str = "market"
    status: str = "filled"
    order_id: str = ""


@dataclass
class Order:
    symbol: str
    side: str
    quantity: float
    price: float
    order_type: str = "limit"
    status: str = "open"
    order_id: str = ""


@dataclass
class SymbolRule:
    min_qty: float = 0.0001
    step_size: float = 0.0001
    min_notional: float = 5.0


@dataclass
class BotState:
    bot_running: bool = True
    auto_trading: bool = False
    mode: str = "paper"
    exchange: str = "binance"
    language: str = "vi"
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT"])
    balance_quote: float = 10000.0
    daily_pnl: float = 0.0
    open_positions: Dict[str, Position] = field(default_factory=dict)
    pending_orders: Dict[str, Order] = field(default_factory=dict)
    last_signal: str = "NONE"
    last_trade: str = "No trade yet"
    heartbeat_ts: float = 0.0
    last_error: str = ""
    allowed_exchanges: List[str] = field(default_factory=lambda: ["paper", "binance", "bybit", "mexc"])
