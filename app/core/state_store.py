from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict

from app.core.models import BotState, Order, Position


logger = logging.getLogger(__name__)


class SQLiteStateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return self._conn

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
        conn = self._connect()
        with self._lock:
            data = {
                "bot_running": state.bot_running,
                "auto_trading": state.auto_trading,
                "mode": state.mode,
                "exchange": state.exchange,
                "language": state.language,
                "symbols": list(state.symbols),
                "default_bot_running": state.default_bot_running,
                "default_auto_trading": state.default_auto_trading,
                "default_mode": state.default_mode,
                "default_exchange": state.default_exchange,
                "default_language": state.default_language,
                "default_symbols": list(state.default_symbols),
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
                "allowed_exchanges": list(state.allowed_exchanges),
            }
            for key, value in data.items():
                conn.execute("REPLACE INTO bot_state(key, value) VALUES(?, ?)", (key, json.dumps(value)))
            conn.commit()
            logger.debug(
                "State persisted to %s mode=%s exchange=%s language=%s symbols=%s",
                self.db_path,
                state.mode,
                state.exchange,
                state.language,
                state.symbols,
            )

    def load_state(self, default: BotState) -> BotState:
        conn = self._connect()
        with self._lock:
            rows = conn.execute("SELECT key, value FROM bot_state").fetchall()
        if not rows:
            logger.info("No saved state found in %s. Using defaults.", self.db_path)
            return default
        raw: Dict[str, Any] = {key: json.loads(value) for key, value in rows}
        positions = {symbol: Position(**payload) for symbol, payload in raw.get("open_positions", {}).items()}
        pending_orders = {order_id: Order(**payload) for order_id, payload in raw.get("pending_orders", {}).items()}
        state = BotState(
            bot_running=raw.get("bot_running", default.bot_running),
            auto_trading=raw.get("auto_trading", default.auto_trading),
            mode=raw.get("mode", default.mode),
            exchange=raw.get("exchange", default.exchange),
            language=raw.get("language", default.language),
            symbols=raw.get("symbols", default.symbols),
            default_bot_running=raw.get("default_bot_running", default.default_bot_running),
            default_auto_trading=raw.get("default_auto_trading", default.default_auto_trading),
            default_mode=raw.get("default_mode", default.default_mode),
            default_exchange=raw.get("default_exchange", default.default_exchange),
            default_language=raw.get("default_language", default.default_language),
            default_symbols=raw.get("default_symbols", default.default_symbols),
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
        logger.info(
            "Loaded state from %s mode=%s exchange=%s language=%s symbols=%s",
            self.db_path,
            state.mode,
            state.exchange,
            state.language,
            state.symbols,
        )
        return state
