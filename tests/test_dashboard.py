from app.exchange.paper import PaperExchange
from app.web.dashboard import _chart_payload, _symbol_for_market


def test_chart_payload_uses_exchange_ohlcv() -> None:
    exchange = PaperExchange(balance_quote=1000, prices={"BTC/USDT": 105.0})
    payload = _chart_payload(exchange, "BTC/USDT", "1m", limit=5)

    assert payload["symbol"] == "BTC/USDT"
    assert payload["timeframe"] == "1m"
    assert len(payload["candles"]) == 5
    assert payload["latest_close"] == payload["candles"][-1]["close"]


def test_symbol_for_future_market_adds_unified_suffix() -> None:
    assert _symbol_for_market("BTC/USDT", "future") == "BTC/USDT:USDT"


def test_symbol_for_spot_market_removes_future_suffix() -> None:
    assert _symbol_for_market("BTC/USDT:USDT", "spot") == "BTC/USDT"
