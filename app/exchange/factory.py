from __future__ import annotations

from app.config.settings import Settings
from app.exchange.ccxt_adapters import BinanceAdapter, BybitAdapter, MexcAdapter
from app.exchange.paper import PaperExchange


SUPPORTED_EXCHANGES = {"paper", "binance", "bybit", "mexc"}


def build_exchange(settings: Settings, mode: str, exchange_name: str):
    exchange_name = exchange_name.lower()
    if exchange_name not in SUPPORTED_EXCHANGES:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    if mode == "paper" or settings.dry_run or exchange_name == "paper":
        return PaperExchange(
            balance_quote=settings.paper_start_balance,
            default_stop_loss_pct=settings.stop_loss_pct,
            default_take_profit_pct=settings.take_profit_pct,
            default_trailing_stop_pct=settings.trailing_stop_pct,
        )
    if exchange_name == "binance":
        return BinanceAdapter(settings.binance, retry_attempts=settings.api_retry_attempts, retry_delay_seconds=settings.api_retry_delay_seconds)
    if exchange_name == "bybit":
        return BybitAdapter(settings.bybit, retry_attempts=settings.api_retry_attempts, retry_delay_seconds=settings.api_retry_delay_seconds)
    if exchange_name == "mexc":
        return MexcAdapter(settings.mexc, retry_attempts=settings.api_retry_attempts, retry_delay_seconds=settings.api_retry_delay_seconds)
    raise ValueError(f"Unsupported exchange: {exchange_name}")
