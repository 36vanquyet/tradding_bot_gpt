from app.exchange.paper import PaperExchange


def test_paper_buy_sell_cycle() -> None:
    ex = PaperExchange(balance_quote=1000, prices={"BTC/USDT": 100})
    buy = ex.create_market_buy("BTC/USDT", 1)
    assert buy.side == "BUY"
    assert "BTC/USDT" in ex.positions
    assert ex.positions["BTC/USDT"].stop_loss is not None
    sell = ex.create_market_sell("BTC/USDT", 1)
    assert sell.side == "SELL"
    assert "BTC/USDT" not in ex.positions
