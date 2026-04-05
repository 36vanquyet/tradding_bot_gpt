from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]


def _resolve_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute() or path_value == ":memory:":
        return str(path)
    return str((BASE_DIR / path).resolve())


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_list(name: str, default: List[str]) -> List[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class ExchangeCredentials:
    api_key: str
    api_secret: str
    testnet: bool


@dataclass(frozen=True)
class Settings:
    app_env: str
    db_path: str
    log_level: str
    dry_run: bool
    default_exchange: str
    default_symbols: List[str]
    default_timeframe: str
    fast_ma: int
    slow_ma: int
    risk_per_trade: float
    paper_start_balance: float
    poll_interval_seconds: int
    heartbeat_seconds: int
    max_open_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    trailing_stop_pct: float
    entry_order_type: str
    limit_price_offset_pct: float
    api_retry_attempts: int
    api_retry_delay_seconds: float
    future_margin_mode: str
    future_leverage: float
    dashboard_enabled: bool
    dashboard_host: str
    dashboard_port: int
    quote_asset: str
    telegram_bot_token: str
    telegram_allowed_user_ids: List[int]
    telegram_chat_id: str
    binance: ExchangeCredentials
    bybit: ExchangeCredentials
    mexc: ExchangeCredentials


def load_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        db_path=_resolve_path(os.getenv("DB_PATH", "bot_state.db")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        dry_run=_get_bool("DRY_RUN", True),
        default_exchange=os.getenv("DEFAULT_EXCHANGE", "binance").lower(),
        default_symbols=_get_list("DEFAULT_SYMBOLS", ["BTC/USDT"]),
        default_timeframe=os.getenv("DEFAULT_TIMEFRAME", "1m"),
        fast_ma=int(os.getenv("FAST_MA", "5")),
        slow_ma=int(os.getenv("SLOW_MA", "20")),
        risk_per_trade=float(os.getenv("RISK_PER_TRADE", "0.01")),
        paper_start_balance=float(os.getenv("PAPER_START_BALANCE", "10000")),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "10")),
        heartbeat_seconds=int(os.getenv("HEARTBEAT_SECONDS", "300")),
        max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "3")),
        stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.02")),
        take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.04")),
        trailing_stop_pct=float(os.getenv("TRAILING_STOP_PCT", "0.01")),
        entry_order_type=os.getenv("ENTRY_ORDER_TYPE", "market").lower(),
        limit_price_offset_pct=float(os.getenv("LIMIT_PRICE_OFFSET_PCT", "0.001")),
        api_retry_attempts=int(os.getenv("API_RETRY_ATTEMPTS", "3")),
        api_retry_delay_seconds=float(os.getenv("API_RETRY_DELAY_SECONDS", "1.0")),
        future_margin_mode=os.getenv("FUTURE_MARGIN_MODE", "cross").lower(),
        future_leverage=float(os.getenv("FUTURE_LEVERAGE", "1")),
        dashboard_enabled=_get_bool("DASHBOARD_ENABLED", True),
        dashboard_host=os.getenv("DASHBOARD_HOST", "127.0.0.1"),
        dashboard_port=int(os.getenv("DASHBOARD_PORT", "8080")),
        quote_asset=os.getenv("QUOTE_ASSET", "USDT"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_allowed_user_ids=[int(x) for x in _get_list("TELEGRAM_ALLOWED_USER_IDS", [])],
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        binance=ExchangeCredentials(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            testnet=_get_bool("BINANCE_TESTNET", True),
        ),
        bybit=ExchangeCredentials(
            api_key=os.getenv("BYBIT_API_KEY", ""),
            api_secret=os.getenv("BYBIT_API_SECRET", ""),
            testnet=_get_bool("BYBIT_TESTNET", True),
        ),
        mexc=ExchangeCredentials(
            api_key=os.getenv("MEXC_API_KEY", ""),
            api_secret=os.getenv("MEXC_API_SECRET", ""),
            testnet=_get_bool("MEXC_TESTNET", False),
        ),
    )
