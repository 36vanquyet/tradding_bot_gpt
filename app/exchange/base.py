from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence

from app.core.models import Order, Position, SymbolRule, Trade


class ExchangeAdapter(ABC):
    name: str

    def configure_futures(self, symbol: str, margin_mode: str | None = None, leverage: float | None = None) -> None:
        return None

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_balance_quote(self, quote: str = "USDT", market_kind: str = "spot") -> float:
        raise NotImplementedError

    @abstractmethod
    def create_market_buy(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        raise NotImplementedError

    @abstractmethod
    def create_market_sell(self, symbol: str, quantity: float, market_kind: str = "spot") -> Trade:
        raise NotImplementedError

    @abstractmethod
    def create_limit_buy(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        raise NotImplementedError

    @abstractmethod
    def create_limit_sell(self, symbol: str, quantity: float, price: float, market_kind: str = "spot") -> Order:
        raise NotImplementedError

    @abstractmethod
    def fetch_positions(self) -> Sequence[Position]:
        raise NotImplementedError

    @abstractmethod
    def fetch_open_orders(self) -> Sequence[Order]:
        raise NotImplementedError

    @abstractmethod
    def sync(self, tracked_symbols: Sequence[str]) -> None:
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
