from __future__ import annotations

import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.core.manual_trading import execute_close_position, execute_manual_order, parse_manual_order_args
from app.exchange.factory import build_exchange
from app.telegram.i18n import normalize_language, t
from app.telegram.keyboards import main_keyboard


def _is_authorized(update: Update, allowed_user_ids: set[int]) -> bool:
    user = update.effective_user
    return bool(user and user.id in allowed_user_ids)


def _current_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    control = context.application.bot_data["control_service"]
    return normalize_language(control.state.language)


def _status_text(control) -> str:
    lang = normalize_language(control.state.language)
    s = control.get_status()
    open_positions = ", ".join(s["open_positions"]) if s["open_positions"] else t(lang, "none")
    return (
        f"<b>{t(lang, 'status_title')}</b>\n"
        f"{t(lang, 'status_running')}: {s['bot_running']}\n"
        f"{t(lang, 'status_auto')}: {s['auto_trading']}\n"
        f"{t(lang, 'status_mode')}: {s['mode']}\n"
        f"{t(lang, 'status_exchange')}: {s['exchange']}\n"
        f"{t(lang, 'status_language')}: {s['language']}\n"
        f"{t(lang, 'status_symbols')}: {', '.join(s['symbols'])}\n"
        f"{t(lang, 'status_balance')}: {s['balance_quote']:.2f} USDT\n"
        f"{t(lang, 'status_open_positions')}: {open_positions}\n"
        f"{t(lang, 'status_daily_pnl')}: {s['daily_pnl']:.2f}\n"
        f"{t(lang, 'status_last_signal')}: {s['last_signal']}\n"
        f"{t(lang, 'status_last_trade')}: {s['last_trade']}\n"
        f"{t(lang, 'status_last_error')}: {s['last_error'] or t(lang, 'none')}"
    )


def _help_text(language: str) -> str:
    return t(language, "help")


def _positions_text(control) -> str:
    lang = normalize_language(control.state.language)
    positions = list(control.state.open_positions.values())
    if not positions:
        return f"<b>{t(lang, 'positions_title')}</b>\n{t(lang, 'none')}"
    lines = [f"<b>{t(lang, 'positions_title')}</b>"]
    for pos in positions:
        lines.append(
            (
                f"{pos.symbol} | qty={pos.quantity:.6f} | entry={pos.entry_price:.2f}"
                f" | sl={pos.stop_loss if pos.stop_loss is not None else '-'}"
                f" | tp={pos.take_profit if pos.take_profit is not None else '-'}"
            )
        )
    return "\n".join(lines)


def _orders_text(control) -> str:
    lang = normalize_language(control.state.language)
    orders = list(control.state.pending_orders.values())
    if not orders:
        return f"<b>{t(lang, 'orders_title')}</b>\n{t(lang, 'none')}"
    lines = [f"<b>{t(lang, 'orders_title')}</b>"]
    for order in orders:
        lines.append(
            (
                f"{order.symbol} | {order.side} | {order.order_type}"
                f" | qty={order.quantity:.6f} | price={order.price:.2f} | status={order.status}"
            )
        )
    return "\n".join(lines)


async def _safe_edit_message(query, text: str, language: str, parse_mode: str | None = None) -> None:
    try:
        await query.edit_message_text(text, parse_mode=parse_mode, reply_markup=main_keyboard(language))
    except BadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        raise


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    language = _current_language(context)
    await update.effective_message.reply_text(t(language, "start"), reply_markup=main_keyboard(language))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    language = _current_language(context)
    await update.effective_message.reply_text(_help_text(language), parse_mode=ParseMode.HTML, reply_markup=main_keyboard(language))


async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    current_language = normalize_language(control.state.language)
    if not context.args:
        await update.effective_message.reply_text(t(current_language, "usage_language"), reply_markup=main_keyboard(current_language))
        return
    requested = normalize_language(context.args[0])
    if context.args[0].lower() not in {"vi", "en"}:
        await update.effective_message.reply_text(t(current_language, "language_invalid"), reply_markup=main_keyboard(current_language))
        return
    control.set_language(requested)
    await update.effective_message.reply_text(t(requested, "language_changed"), reply_markup=main_keyboard(requested))


async def reset_config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    control.reset_runtime_config()
    exchange = build_exchange(settings, control.state.mode, control.state.exchange)
    engine.set_exchange(exchange)
    context.application.bot_data["exchange"] = exchange
    language = normalize_language(control.state.language)
    await update.effective_message.reply_text(t(language, "config_reset"), reply_markup=main_keyboard(language))


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    await update.effective_message.reply_text(_status_text(control), parse_mode=ParseMode.HTML, reply_markup=main_keyboard(control.state.language))


async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    s = control.get_status()
    age = max(time.time() - float(s["heartbeat_ts"] or 0), 0.0)
    health_status = t(language, "health_ok") if age < 2 * context.application.bot_data["poll_interval_seconds"] else t(language, "health_stale")
    text = f"{t(language, 'health_age', age=age)}\n{t(language, 'health_status', status=health_status)}"
    await update.effective_message.reply_text(text, reply_markup=main_keyboard(language))


async def symbols_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    await update.effective_message.reply_text(
        t(language, "symbols", symbols=", ".join(control.state.symbols)),
        reply_markup=main_keyboard(language),
    )


async def positions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    engine = context.application.bot_data["engine"]
    engine.sync_positions_into_state()
    await update.effective_message.reply_text(
        _positions_text(control),
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(control.state.language),
    )


async def orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    engine = context.application.bot_data["engine"]
    engine.sync_positions_into_state()
    await update.effective_message.reply_text(
        _orders_text(control),
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(control.state.language),
    )


async def exchange_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if not context.args:
        await update.effective_message.reply_text(t(language, "usage_exchange"), reply_markup=main_keyboard(language))
        return
    requested = context.args[0].lower()
    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    exchange = build_exchange(settings, control.state.mode, requested)
    engine.set_exchange(exchange)
    control.set_exchange(requested)
    context.application.bot_data["exchange"] = exchange
    await update.effective_message.reply_text(t(language, "exchange_changed", exchange=requested), reply_markup=main_keyboard(language))


async def order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if len(context.args) < 4:
        await update.effective_message.reply_text(t(language, "usage_order"), reply_markup=main_keyboard(language))
        return

    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    exchange = context.application.bot_data["exchange"]
    try:
        request = parse_manual_order_args(context.args)
        message = execute_manual_order(request, settings, control, engine, exchange)
    except Exception as exc:
        control.set_error(str(exc))
        await update.effective_message.reply_text(str(exc), reply_markup=main_keyboard(language))
        return
    await update.effective_message.reply_text(message, reply_markup=main_keyboard(language))


async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _manual_order_cmd(update, context, side_override="buy")


async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _manual_order_cmd(update, context, side_override="sell")


async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if len(context.args) < 2:
        await update.effective_message.reply_text(t(language, "usage_close"), reply_markup=main_keyboard(language))
        return

    market_kind = context.args[0].lower()
    symbol = context.args[1].upper()
    quantity = float(context.args[2]) if len(context.args) > 2 else None
    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    exchange = context.application.bot_data["exchange"]
    try:
        message = execute_close_position(market_kind, symbol, settings, control, engine, exchange, quantity=quantity)
    except Exception as exc:
        control.set_error(str(exc))
        await update.effective_message.reply_text(str(exc), reply_markup=main_keyboard(language))
        return
    await update.effective_message.reply_text(message, reply_markup=main_keyboard(language))


async def _manual_order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, side_override: str) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if len(context.args) < 3:
        await update.effective_message.reply_text(t(language, f"usage_{side_override}"), reply_markup=main_keyboard(language))
        return

    settings = context.application.bot_data["settings"]
    engine = context.application.bot_data["engine"]
    exchange = context.application.bot_data["exchange"]
    try:
        request = parse_manual_order_args(context.args, side_override=side_override)
        message = execute_manual_order(request, settings, control, engine, exchange)
    except Exception as exc:
        control.set_error(str(exc))
        await update.effective_message.reply_text(str(exc), reply_markup=main_keyboard(language))
        return
    await update.effective_message.reply_text(message, reply_markup=main_keyboard(language))


async def add_symbol_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if not context.args:
        await update.effective_message.reply_text(t(language, "usage_addsymbol"), reply_markup=main_keyboard(language))
        return
    symbol = context.args[0].upper()
    control.add_symbol(symbol)
    await update.effective_message.reply_text(t(language, "symbol_added", symbol=symbol), reply_markup=main_keyboard(language))


async def rem_symbol_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await update.effective_message.reply_text(t("vi", "unauthorized"))
        return
    control = context.application.bot_data["control_service"]
    language = normalize_language(control.state.language)
    if not context.args:
        await update.effective_message.reply_text(t(language, "usage_remsymbol"), reply_markup=main_keyboard(language))
        return
    symbol = context.args[0].upper()
    control.remove_symbol(symbol)
    await update.effective_message.reply_text(t(language, "symbol_removed", symbol=symbol), reply_markup=main_keyboard(language))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    allowed = set(context.application.bot_data["allowed_user_ids"])
    if not _is_authorized(update, allowed):
        await _safe_edit_message(query, t("vi", "unauthorized"), "vi")
        return

    control = context.application.bot_data["control_service"]
    exchange = context.application.bot_data["exchange"]
    data = query.data
    language = normalize_language(control.state.language)

    if data == "status":
        await _safe_edit_message(query, _status_text(control), language, parse_mode=ParseMode.HTML)
    elif data == "health":
        s = control.get_status()
        age = max(time.time() - float(s["heartbeat_ts"] or 0), 0.0)
        health_status = t(language, "health_ok") if age < 2 * context.application.bot_data["poll_interval_seconds"] else t(language, "health_stale")
        text = f"{t(language, 'health_age', age=age)}\n{t(language, 'health_status', status=health_status)}"
        await _safe_edit_message(query, text, language)
    elif data == "auto_on":
        control.enable_auto()
        await _safe_edit_message(query, t(language, "auto_on"), language)
    elif data == "auto_off":
        control.disable_auto()
        await _safe_edit_message(query, t(language, "auto_off"), language)
    elif data == "pause":
        control.pause_bot()
        await _safe_edit_message(query, t(language, "bot_paused"), language)
    elif data == "resume":
        control.resume_bot()
        await _safe_edit_message(query, t(language, "bot_resumed"), language)
    elif data == "mode_paper":
        settings = context.application.bot_data["settings"]
        engine = context.application.bot_data["engine"]
        control.set_mode("paper")
        new_exchange = build_exchange(settings, "paper", control.state.exchange)
        engine.set_exchange(new_exchange)
        context.application.bot_data["exchange"] = new_exchange
        await _safe_edit_message(query, t(language, "mode_paper"), language)
    elif data == "mode_live":
        settings = context.application.bot_data["settings"]
        engine = context.application.bot_data["engine"]
        control.set_mode("live")
        new_exchange = build_exchange(settings, "live", control.state.exchange)
        engine.set_exchange(new_exchange)
        context.application.bot_data["exchange"] = new_exchange
        await _safe_edit_message(query, t(language, "mode_live"), language)
    elif data == "lang_vi":
        control.set_language("vi")
        await _safe_edit_message(query, t("vi", "language_changed"), "vi")
    elif data == "lang_en":
        control.set_language("en")
        await _safe_edit_message(query, t("en", "language_changed"), "en")
    elif data == "close_all":
        try:
            trades = exchange.close_all()
            control.state.last_trade = t(language, "close_all", count=len(trades))
            control.persist_engine_state()
            await _safe_edit_message(query, control.state.last_trade, language)
        except Exception as exc:
            control.set_error(str(exc))
            await _safe_edit_message(query, str(exc), language)
