from __future__ import annotations


SUPPORTED_LANGUAGES = {"vi", "en"}


MESSAGES = {
    "vi": {
        "unauthorized": "Bạn không có quyền sử dụng bot này.",
        "start": "Trading bot v5 đã sẵn sàng.\nDùng /help để xem hướng dẫn đầy đủ và các lệnh hỗ trợ.",
        "help": (
            "<b>Hướng dẫn sử dụng</b>\n"
            "/start - Mở bot và hiện keyboard thao tác nhanh\n"
            "/help - Xem hướng dẫn các tính năng\n"
            "/status - Xem trạng thái bot, mode, exchange, ngôn ngữ, số dư và lệnh gần nhất\n"
            "/health - Kiểm tra heartbeat của engine\n"
            "/symbols - Xem danh sách symbol đang theo dõi\n"
            "/exchange &lt;paper|binance|bybit|mexc&gt; - Đổi sàn giao dịch\n"
            "/language &lt;vi|en&gt; - Đổi ngôn ngữ chatbot\n"
            "/lang &lt;vi|en&gt; - Alias ngắn gọn của /language\n"
            "/resetconfig - Reset cấu hình runtime về mặc định\n"
            "/addsymbol BTC/USDT - Thêm symbol vào danh sách theo dõi\n"
            "/remsymbol BTC/USDT - Xóa symbol khỏi danh sách theo dõi\n"
            "\n"
            "<b>Lưu ý</b>\n"
            "- Bot giữ lại cấu hình runtime hiện tại sau khi restart\n"
            "- Dùng /resetconfig để quay về cấu hình mặc định lấy từ file .env\n"
            "- Khi DRY_RUN=true, bot vẫn dùng PaperExchange để mô phỏng"
        ),
        "status_title": "Status",
        "status_running": "Đang chạy",
        "status_auto": "Auto Trading",
        "status_mode": "Mode",
        "status_exchange": "Exchange",
        "status_language": "Ngôn ngữ",
        "status_symbols": "Symbols",
        "status_balance": "Số dư",
        "status_open_positions": "Lệnh đang mở",
        "status_daily_pnl": "Daily PnL",
        "status_last_signal": "Tín hiệu gần nhất",
        "status_last_trade": "Lệnh gần nhất",
        "status_last_error": "Lỗi gần nhất",
        "none": "Không có",
        "health_age": "Độ trễ heartbeat: {age:.1f}s",
        "health_status": "Trạng thái engine: {status}",
        "health_ok": "OK",
        "health_stale": "STALE",
        "symbols": "Symbols: {symbols}",
        "usage_exchange": "Cách dùng: /exchange <paper|binance|bybit|mexc>",
        "usage_addsymbol": "Cách dùng: /addsymbol BTC/USDT",
        "usage_remsymbol": "Cách dùng: /remsymbol BTC/USDT",
        "usage_language": "Cách dùng: /language <vi|en> hoặc /lang <vi|en>",
        "config_reset": "Đã reset cấu hình runtime về mặc định.",
        "exchange_changed": "Đã chuyển exchange sang: {exchange}",
        "symbol_added": "Đã thêm symbol: {symbol}",
        "symbol_removed": "Đã xóa symbol: {symbol}",
        "auto_on": "Đã bật auto trading",
        "auto_off": "Đã tắt auto trading",
        "bot_paused": "Bot đã pause",
        "bot_resumed": "Bot đã resume",
        "mode_paper": "Đã chuyển sang paper mode",
        "mode_live": "Đã chuyển sang live mode",
        "close_all": "close_all executed: {count} trades",
        "language_changed": "Đã chuyển ngôn ngữ sang Tiếng Việt.",
        "language_invalid": "Ngôn ngữ không hợp lệ. Chỉ hỗ trợ: vi, en.",
        "keyboard_status": "Trạng thái",
        "keyboard_health": "Sức khỏe",
        "keyboard_auto_on": "Bật Auto",
        "keyboard_auto_off": "Tắt Auto",
        "keyboard_pause": "Tạm dừng",
        "keyboard_resume": "Tiếp tục",
        "keyboard_mode_paper": "Mode: Paper",
        "keyboard_mode_live": "Mode: Live",
        "keyboard_language_vi": "Tiếng Việt",
        "keyboard_language_en": "English",
        "keyboard_close_all": "Đóng tất cả",
        "keyboard_language_row": "Ngôn ngữ",
        "lang_vi_name": "Tiếng Việt",
        "lang_en_name": "Tiếng Anh",
    },
    "en": {
        "unauthorized": "You are not authorized to use this bot.",
        "start": "Trading bot v5 is ready.\nUse /help to see the full guide and supported commands.",
        "help": (
            "<b>User Guide</b>\n"
            "/start - Open the bot and show the quick action keyboard\n"
            "/help - Show the feature guide\n"
            "/status - Show bot status, mode, exchange, language, balance, and latest activity\n"
            "/health - Check the engine heartbeat\n"
            "/symbols - Show tracked symbols\n"
            "/exchange &lt;paper|binance|bybit|mexc&gt; - Change exchange\n"
            "/language &lt;vi|en&gt; - Change chatbot language\n"
            "/lang &lt;vi|en&gt; - Short alias for /language\n"
            "/resetconfig - Reset runtime config to defaults\n"
            "/addsymbol BTC/USDT - Add a symbol to the watchlist\n"
            "/remsymbol BTC/USDT - Remove a symbol from the watchlist\n"
            "\n"
            "<b>Notes</b>\n"
            "- The bot keeps the current runtime config after restart\n"
            "- Use /resetconfig to restore defaults from .env\n"
            "- When DRY_RUN=true, the bot still uses PaperExchange for simulation"
        ),
        "status_title": "Status",
        "status_running": "Running",
        "status_auto": "Auto Trading",
        "status_mode": "Mode",
        "status_exchange": "Exchange",
        "status_language": "Language",
        "status_symbols": "Symbols",
        "status_balance": "Balance",
        "status_open_positions": "Open Positions",
        "status_daily_pnl": "Daily PnL",
        "status_last_signal": "Last Signal",
        "status_last_trade": "Last Trade",
        "status_last_error": "Last Error",
        "none": "None",
        "health_age": "Heartbeat age: {age:.1f}s",
        "health_status": "Engine status: {status}",
        "health_ok": "OK",
        "health_stale": "STALE",
        "symbols": "Symbols: {symbols}",
        "usage_exchange": "Usage: /exchange <paper|binance|bybit|mexc>",
        "usage_addsymbol": "Usage: /addsymbol BTC/USDT",
        "usage_remsymbol": "Usage: /remsymbol BTC/USDT",
        "usage_language": "Usage: /language <vi|en> or /lang <vi|en>",
        "config_reset": "Runtime config has been reset to defaults.",
        "exchange_changed": "Exchange switched to: {exchange}",
        "symbol_added": "Added symbol: {symbol}",
        "symbol_removed": "Removed symbol: {symbol}",
        "auto_on": "Auto trading enabled",
        "auto_off": "Auto trading disabled",
        "bot_paused": "Bot paused",
        "bot_resumed": "Bot resumed",
        "mode_paper": "Switched to paper mode",
        "mode_live": "Switched to live mode",
        "close_all": "close_all executed: {count} trades",
        "language_changed": "Language switched to English.",
        "language_invalid": "Invalid language. Supported values: vi, en.",
        "keyboard_status": "Status",
        "keyboard_health": "Health",
        "keyboard_auto_on": "Auto ON",
        "keyboard_auto_off": "Auto OFF",
        "keyboard_pause": "Pause",
        "keyboard_resume": "Resume",
        "keyboard_mode_paper": "Mode: Paper",
        "keyboard_mode_live": "Mode: Live",
        "keyboard_language_vi": "Tiếng Việt",
        "keyboard_language_en": "English",
        "keyboard_close_all": "Close All",
        "keyboard_language_row": "Language",
        "lang_vi_name": "Vietnamese",
        "lang_en_name": "English",
    },
}


def normalize_language(language: str | None) -> str:
    language = (language or "vi").lower()
    return language if language in SUPPORTED_LANGUAGES else "vi"


def t(language: str | None, key: str, **kwargs) -> str:
    lang = normalize_language(language)
    template = MESSAGES[lang][key]
    return template.format(**kwargs) if kwargs else template
