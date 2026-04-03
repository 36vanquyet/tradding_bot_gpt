from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict

from app.core.models import BotState, Order, Position


class SQLiteStateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False) if self.db_path == ":memory:" else None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_state(self, state: BotState) -> None:
        data = {
            "bot_running": state.bot_running,
            "auto_trading": state.auto_trading,
            "mode": state.mode,
            "exchange": state.exchange,
            "language": state.language,
            "symbols": state.symbols,
            "balance_quote": state.balance_quote,
            "daily_pnl": state.daily_pnl,
            "open_positions": {
                symbol: {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                    "highest_price": pos.highest_price,
                    "trailing_stop_pct": pos.trailing_stop_pct,
                    "source": pos.source,
                }
                for symbol, pos in state.open_positions.items()
            },
            "pending_orders": {
                order_id: {
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": order.quantity,
                    "price": order.price,
                    "order_type": order.order_type,
                    "status": order.status,
                    "order_id": order.order_id,
                }
                for order_id, order in state.pending_orders.items()
            },
            "last_signal": state.last_signal,
            "last_trade": state.last_trade,
            "heartbeat_ts": state.heartbeat_ts,
            "last_error": state.last_error,
            "allowed_exchanges": state.allowed_exchanges,
        }
        conn = self._connect()
        with self._lock:
            for key, value in data.items():
                conn.execute("REPLACE INTO bot_state(key, value) VALUES(?, ?)", (key, json.dumps(value)))
            conn.commit()

    def load_state(self, default: BotState) -> BotState:
        conn = self._connect()
        with self._lock:
            rows = conn.execute("SELECT key, value FROM bot_state").fetchall()
        if not rows:
            return default
        raw: Dict[str, Any] = {key: json.loads(value) for key, value in rows}
        positions = {symbol: Position(**payload) for symbol, payload in raw.get("open_positions", {}).items()}
        pending_orders = {order_id: Order(**payload) for order_id, payload in raw.get("pending_orders", {}).items()}
        return BotState(
            bot_running=raw.get("bot_running", default.bot_running),
            auto_trading=raw.get("auto_trading", default.auto_trading),
            mode=raw.get("mode", default.mode),
            exchange=raw.get("exchange", default.exchange),
            language=raw.get("language", default.language),
            symbols=raw.get("symbols", default.symbols),
            balance_quote=raw.get("balance_quote", default.balance_quote),
            daily_pnl=raw.get("daily_pnl", default.daily_pnl),
            open_positions=positions,
            pending_orders=pending_orders,
            last_signal=raw.get("last_signal", default.last_signal),
            last_trade=raw.get("last_trade", default.last_trade),
            heartbeat_ts=raw.get("heartbeat_ts", default.heartbeat_ts),
            last_error=raw.get("last_error", default.last_error),
            allowed_exchanges=raw.get("allowed_exchanges", default.allowed_exchanges),
        )
