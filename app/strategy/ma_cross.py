from __future__ import annotations


class MovingAverageCrossStrategy:
    def __init__(self, fast_ma: int, slow_ma: int) -> None:
        if fast_ma >= slow_ma:
            raise ValueError("fast_ma must be smaller than slow_ma")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma

    @staticmethod
    def _sma(values: list[float], window: int) -> float:
        if len(values) < window:
            return 0.0
        return sum(values[-window:]) / window

    def generate_signal(self, closes: list[float]) -> str:
        if len(closes) < self.slow_ma + 1:
            return "HOLD"
        fast_prev = sum(closes[-self.fast_ma - 1 : -1]) / self.fast_ma
        slow_prev = sum(closes[-self.slow_ma - 1 : -1]) / self.slow_ma
        fast_now = self._sma(closes, self.fast_ma)
        slow_now = self._sma(closes, self.slow_ma)
        if fast_prev <= slow_prev and fast_now > slow_now:
            return "BUY"
        if fast_prev >= slow_prev and fast_now < slow_now:
            return "SELL"
        return "HOLD"
