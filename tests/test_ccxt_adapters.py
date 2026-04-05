from app.exchange.ccxt_adapters import CCXTAdapter


def test_detects_min_amount_precision_error() -> None:
    exc = Exception("bybit amount of BTC/USDT must be greater than minimum amount precision of 0.000001")
    assert CCXTAdapter._is_min_amount_error(exc) is True


def test_ignores_other_exchange_errors() -> None:
    exc = Exception('bybit {"retCode":170131,"retMsg":"Insufficient balance."}')
    assert CCXTAdapter._is_min_amount_error(exc) is False
