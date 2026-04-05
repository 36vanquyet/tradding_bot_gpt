from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.telegram.handlers import (
    add_symbol_cmd,
    button_handler,
    buy_cmd,
    close_cmd,
    exchange_cmd,
    health_cmd,
    help_cmd,
    language_cmd,
    order_cmd,
    orders_cmd,
    positions_cmd,
    rem_symbol_cmd,
    reset_config_cmd,
    sell_cmd,
    start_cmd,
    status_cmd,
    symbols_cmd,
)

logger = logging.getLogger(__name__)


async def app_error_handler(_update, context) -> None:
    logger.exception("Telegram update handling failed", exc_info=context.error)


def build_telegram_app(
    token: str,
    control_service,
    exchange,
    allowed_user_ids,
    poll_interval_seconds: int,
    settings,
    engine,
):
    app = Application.builder().token(token).build()
    app.bot_data["control_service"] = control_service
    app.bot_data["exchange"] = exchange
    app.bot_data["allowed_user_ids"] = allowed_user_ids
    app.bot_data["poll_interval_seconds"] = poll_interval_seconds
    app.bot_data["settings"] = settings
    app.bot_data["engine"] = engine

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("lang", language_cmd))
    app.add_handler(CommandHandler("resetconfig", reset_config_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("symbols", symbols_cmd))
    app.add_handler(CommandHandler("positions", positions_cmd))
    app.add_handler(CommandHandler("orders", orders_cmd))
    app.add_handler(CommandHandler("exchange", exchange_cmd))
    app.add_handler(CommandHandler("order", order_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("addsymbol", add_symbol_cmd))
    app.add_handler(CommandHandler("remsymbol", rem_symbol_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(app_error_handler)
    return app
