from __future__ import annotations

import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.exchange.factory import build_exchange
from app.telegram.keyboards import main_keyboard


def _is_authorized(update: Update, allowed_user_ids: set[int]) -> bool:
    user = update.effective_user
    return bool(user and user.id in allowed_user_ids)


def _status_text(control) -> str:
    s = control.get_status()
    return (
        f"<b>Status</b>\n"
        f"Running: {s['bot_running']}\n"
        f"Auto Trading: {s['auto_trading']}\n"
        f"Mode: {s['mode']}\n"
        f"Exchange: {s['exchange']}\n"
        f"Symbols: {', '.join(s['symbols'])}\n"
        f"Balance: {s['balance_quote']:.2f} USDT\n"
        f"Open Positions: {', '.join(s['open_positions']) if s['open_positions'] else 'None'}\n"
        f"Daily PnL: {s['daily_pnl']:.2f}\n"
        f"Last Signal: {s['last_signal']}\n"
        f"Last Trade: {s['last_trade']}\n"
        f"Last Error: {s['last_error'] or 'None'}"
    )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    text = (
        "Trading bot v4 đã sẵn sàng.\n"
        "Lệnh mới: /exchange <paper|binance|bybit|mexc>, /symbols, /addsymbol BTC/USDT, /remsymbol BTC/USDT"
    )
    await update.effective_message.reply_text(text, reply_markup=main_keyboard())


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    control = context.application.bot_data["control_service"]
    await update.effective_message.reply_text(_status_text(control), parse_mode=ParseMode.HTML)


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    control = context.application.bot_data["control_service"]
    s = control.get_status()
    age = max(time.time() - float(s["heartbeat_ts"] or 0), 0.0)
    text = (
        f"Heartbeat age: {age:.1f}s\n"
        f"Engine status: {'OK' if age < 2 * context.application.bot_data['poll_interval_seconds'] else 'STALE'}"
    )
    await update.effective_message.reply_text(text)


async def symbols_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    control = context.application.bot_data["control_service"]
    await update.effective_message.reply_text("Symbols: " + ", ".join(control.state.symbols))


async def exchange_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /exchange <paper|binance|bybit|mexc>")
        return
    requested = context.args[0].lower()
    control = context.application.bot_data["control_service"]
    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    exchange = build_exchange(settings, control.state.mode, requested)
    engine.set_exchange(exchange)
    control.set_exchange(requested)
    context.application.bot_data["exchange"] = exchange
    await update.effective_message.reply_text(f"Đã chuyển exchange sang: {requested}")


async def add_symbol_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /addsymbol BTC/USDT")
        return
    control = context.application.bot_data["control_service"]
    control.add_symbol(context.args[0])
    await update.effective_message.reply_text("Đã thêm symbol: " + context.args[0].upper())


async def rem_symbol_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text("Unauthorized")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /remsymbol BTC/USDT")
        return
    control = context.application.bot_data["control_service"]
    control.remove_symbol(context.args[0])
    await update.effective_message.reply_text("Đã xoá symbol: " + context.args[0].upper())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await query.edit_message_text("Unauthorized")
        return

    control = context.application.bot_data["control_service"]
    exchange = context.application.bot_data["exchange"]
    data = query.data

    if data == "status":
        await query.edit_message_text(_status_text(control), parse_mode=ParseMode.HTML, reply_markup=main_keyboard())
    elif data == "health":
        s = control.get_status()
        age = max(time.time() - float(s["heartbeat_ts"] or 0), 0.0)
        await query.edit_message_text(f"Heartbeat age={age:.1f}s", reply_markup=main_keyboard())
    elif data == "auto_on":
        control.enable_auto()
        await query.edit_message_text("Đã bật auto trading", reply_markup=main_keyboard())
    elif data == "auto_off":
        control.disable_auto()
        await query.edit_message_text("Đã tắt auto trading", reply_markup=main_keyboard())
    elif data == "pause":
        control.pause_bot()
        await query.edit_message_text("Bot đã pause", reply_markup=main_keyboard())
    elif data == "resume":
        control.resume_bot()
        await query.edit_message_text("Bot đã resume", reply_markup=main_keyboard())
    elif data == "mode_paper":
        settings = context.application.bot_data["settings"]
        engine = context.application.bot_data["engine"]
        control.set_mode("paper")
        new_exchange = build_exchange(settings, "paper", control.state.exchange)
        engine.set_exchange(new_exchange)
        context.application.bot_data["exchange"] = new_exchange
        await query.edit_message_text("Đã chuyển sang paper mode", reply_markup=main_keyboard())
    elif data == "mode_live":
        settings = context.application.bot_data["settings"]
        engine = context.application.bot_data["engine"]
        control.set_mode("live")
        new_exchange = build_exchange(settings, "live", control.state.exchange)
        engine.set_exchange(new_exchange)
        context.application.bot_data["exchange"] = new_exchange
        await query.edit_message_text("Đã chuyển sang live mode", reply_markup=main_keyboard())
    elif data == "close_all":
        trades = exchange.close_all()
        control.state.last_trade = f"close_all executed: {len(trades)} trades"
        control.persist()
        await query.edit_message_text(control.state.last_trade, reply_markup=main_keyboard())
