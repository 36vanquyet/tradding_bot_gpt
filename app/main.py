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
from app.web.dashboard import start_dashboard

logger = logging.getLogger(__name__)


async def _run_engine(engine: TradingEngine) -> None:
    await engine.run_forever()


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    store = SQLiteStateStore(settings.db_path)
    initial_state = BotState(
        bot_running=True,
        auto_trading=False,
        mode="paper" if settings.dry_run else "live",
        exchange=settings.default_exchange,
        language="vi",
        symbols=settings.default_symbols,
        default_bot_running=True,
        default_auto_trading=False,
        default_mode="paper" if settings.dry_run else "live",
        default_exchange=settings.default_exchange,
        default_language="vi",
        default_symbols=settings.default_symbols,
        balance_quote=settings.paper_start_balance,
    )
    state = store.load_state(initial_state)
    control = ControlService(state, store)
    exchange = build_exchange(settings, state.mode, state.exchange)
    strategy = MovingAverageCrossStrategy(settings.fast_ma, settings.slow_ma)
    risk = FixedFractionalRisk(settings.risk_per_trade)
    notifier = TelegramNotifier()
    engine = TradingEngine(settings, control, exchange, strategy, risk, notifier)
    dashboard_server = None

    if settings.dashboard_enabled:
        dashboard_server = start_dashboard(control, settings.dashboard_host, settings.dashboard_port)
        logger.info("Dashboard running at http://%s:%s", settings.dashboard_host, settings.dashboard_port)

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
        try:
            thread.join()
        finally:
            if dashboard_server is not None:
                dashboard_server.shutdown()


if __name__ == "__main__":
    main()
