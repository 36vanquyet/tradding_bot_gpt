from __future__ import annotations

import asyncio
import logging
import threading

from app.config.settings import load_settings
from app.core.control_service import ControlService
from app.core.engine import TradingEngine
from app.core.models import BotState
from app.core.risk import FixedFractionalRisk
from app.core.state_store import SQLiteStateStore
from app.exchange.factory import build_exchange
from app.strategy.ma_cross import MovingAverageCrossStrategy
from app.telegram.bot import build_telegram_app
from app.telegram.notifier import TelegramNotifier
from app.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def _run_engine(engine: TradingEngine) -> None:
    await engine.run_forever()


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    store = SQLiteStateStore(settings.db_path)
    initial_state = BotState(
        mode="paper" if settings.dry_run else "live",
        exchange=settings.default_exchange,
        symbols=settings.default_symbols,
        balance_quote=settings.paper_start_balance,
    )
    state = store.load_state(initial_state)
    control = ControlService(state, store)
    exchange = build_exchange(settings, state.mode, state.exchange)
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    notifier = TelegramNotifier()
    engine = TradingEngine(settings, control, exchange, strategy, risk, notifier)

    application = None
    if settings.telegram_bot_token:
        application = build_telegram_app(
            token=settings.telegram_bot_token,
            control_service=control,
            exchange=exchange,
            allowed_user_ids=settings.telegram_allowed_user_ids,
            poll_interval_seconds=settings.poll_interval_seconds,
            settings=settings,
            engine=engine,
        )
        notifier = TelegramNotifier(application=application, chat_id=settings.telegram_chat_id or None)
        engine.notifier = notifier

    thread = threading.Thread(target=lambda: asyncio.run(_run_engine(engine)), daemon=True)
    thread.start()

    if application:
        application.run_polling()
    else:
        logger.info("Telegram token missing. Engine running without Telegram. Press Ctrl+C to stop.")
        thread.join()


if __name__ == "__main__":
    main()
