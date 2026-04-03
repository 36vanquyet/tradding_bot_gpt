from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from app.telegram.handlers import (
    add_symbol_cmd,
    button_handler,
    exchange_cmd,
    health_cmd,
    rem_symbol_cmd,
    start_cmd,
    status_cmd,
    symbols_cmd,
)


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
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("symbols", symbols_cmd))
    app.add_handler(CommandHandler("exchange", exchange_cmd))
    app.add_handler(CommandHandler("addsymbol", add_symbol_cmd))
    app.add_handler(CommandHandler("remsymbol", rem_symbol_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    return app
