from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

from app.core.models import Position, SymbolRule, Trade


class ExchangeAdapter(ABC):
    name: str

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_balance_quote(self, quote: str = "USDT") -> float:
        raise NotImplementedError

    @abstractmethod
    def create_market_buy(self, symbol: str, quantity: float) -> Trade:
        raise NotImplementedError

    @abstractmethod
    def create_market_sell(self, symbol: str, quantity: float) -> Trade:
        raise NotImplementedError

    @abstractmethod
    def fetch_positions(self) -> Sequence[Position]:
        raise NotImplementedError

    @abstractmethod
    def close_all(self) -> list[Trade]:
        raise NotImplementedError

    @abstractmethod
    def fetch_symbol_rule(self, symbol: str) -> SymbolRule:
        raise NotImplementedError

    @abstractmethod
    def fetch_ticker_price(self, symbol: str) -> float:
        raise NotImplementedError
