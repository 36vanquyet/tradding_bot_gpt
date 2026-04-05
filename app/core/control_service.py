from __future__ import annotations

import threading
import time
from typing import Dict, List

from app.core.models import BotState
from app.core.state_store import SQLiteStateStore


class ControlService:
    def __init__(self, state: BotState, store: SQLiteStateStore) -> None:
        self.state = state
        self.store = store
        self._lock = threading.Lock()
        self.persist()

    def persist(self) -> None:
        self.store.save_state(self.state)

    def persist_runtime_config(self) -> None:
        self.store.save_runtime_config(self.state)

    def persist_engine_state(self) -> None:
        self.store.save_engine_state(self.state)

    def get_status(self) -> Dict[str, object]:
        with self._lock:
            return {
                "bot_running": self.state.bot_running,
                "auto_trading": self.state.auto_trading,
                "mode": self.state.mode,
                "exchange": self.state.exchange,
                "language": self.state.language,
                "symbols": list(self.state.symbols),
                "balance_quote": self.state.balance_quote,
                "daily_pnl": self.state.daily_pnl,
                "open_positions": list(self.state.open_positions.keys()),
                "pending_orders": list(self.state.pending_orders.keys()),
                "last_signal": self.state.last_signal,
                "last_trade": self.state.last_trade,
                "heartbeat_ts": self.state.heartbeat_ts,
                "last_error": self.state.last_error,
            }

    def get_runtime_config(self) -> Dict[str, object]:
        with self._lock:
            return {
                "bot_running": self.state.bot_running,
                "auto_trading": self.state.auto_trading,
                "mode": self.state.mode,
                "exchange": self.state.exchange,
                "language": self.state.language,
                "symbols": list(self.state.symbols),
            }

    def pause_bot(self) -> None:
        with self._lock:
            self.state.bot_running = False
            self.persist_runtime_config()

    def resume_bot(self) -> None:
        with self._lock:
            self.state.bot_running = True
            self.persist_runtime_config()

    def enable_auto(self) -> None:
        with self._lock:
            self.state.auto_trading = True
            self.persist_runtime_config()

    def disable_auto(self) -> None:
        with self._lock:
            self.state.auto_trading = False
            self.persist_runtime_config()

    def set_mode(self, mode: str) -> None:
        if mode not in {"paper", "live"}:
            raise ValueError("mode must be 'paper' or 'live'")
        with self._lock:
            self.state.mode = mode
            self.persist_runtime_config()

    def set_exchange(self, exchange: str) -> None:
        exchange = exchange.lower()
        if exchange not in self.state.allowed_exchanges:
            raise ValueError(f"Unsupported exchange: {exchange}")
        with self._lock:
            self.state.exchange = exchange
            self.persist_runtime_config()

    def set_language(self, language: str) -> None:
        language = language.lower()
        if language not in {"vi", "en"}:
            raise ValueError("language must be 'vi' or 'en'")
        with self._lock:
            self.state.language = language
            self.persist_runtime_config()

    def set_symbols(self, symbols: List[str]) -> None:
        cleaned = [s.strip().upper() for s in symbols if s.strip()]
        if not cleaned:
            raise ValueError("symbols cannot be empty")
        with self._lock:
            self.state.symbols = cleaned
            self.persist_runtime_config()

    def add_symbol(self, symbol: str) -> None:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol cannot be empty")
        with self._lock:
            if symbol not in self.state.symbols:
                self.state.symbols.append(symbol)
            self.persist_runtime_config()

    def remove_symbol(self, symbol: str) -> None:
        symbol = symbol.strip().upper()
        with self._lock:
            self.state.symbols = [s for s in self.state.symbols if s != symbol]
            self.persist_runtime_config()

    def set_heartbeat(self) -> None:
        with self._lock:
            self.state.heartbeat_ts = time.time()
            self.persist_engine_state()

    def set_error(self, message: str) -> None:
        with self._lock:
            self.state.last_error = message
            self.persist_engine_state()

    def reset_runtime_config(self) -> None:
        with self._lock:
            self.state.bot_running = self.state.default_bot_running
            self.state.auto_trading = self.state.default_auto_trading
            self.state.mode = self.state.default_mode
            self.state.exchange = self.state.default_exchange
            self.state.language = self.state.default_language
            self.state.symbols = list(self.state.default_symbols)
            self.persist_runtime_config()
