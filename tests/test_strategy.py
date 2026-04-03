from app.strategy.ma_cross import MovingAverageCrossStrategy


def test_generate_buy_or_hold_signal_returns_string() -> None:
    strategy = MovingAverageCrossStrategy(3, 5)
    closes = [1, 1, 1, 1, 1, 2, 3, 4]
    assert strategy.generate_signal(closes) in {"BUY", "SELL", "HOLD"}
