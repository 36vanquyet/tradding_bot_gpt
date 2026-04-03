from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.telegram.i18n import t


def main_keyboard(language: str = "vi") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t(language, "keyboard_status"), callback_data="status"),
                InlineKeyboardButton(t(language, "keyboard_health"), callback_data="health"),
            ],
            [
                InlineKeyboardButton(t(language, "keyboard_auto_on"), callback_data="auto_on"),
                InlineKeyboardButton(t(language, "keyboard_auto_off"), callback_data="auto_off"),
            ],
            [
                InlineKeyboardButton(t(language, "keyboard_pause"), callback_data="pause"),
                InlineKeyboardButton(t(language, "keyboard_resume"), callback_data="resume"),
            ],
            [
                InlineKeyboardButton(t(language, "keyboard_mode_paper"), callback_data="mode_paper"),
                InlineKeyboardButton(t(language, "keyboard_mode_live"), callback_data="mode_live"),
            ],
            [
                InlineKeyboardButton(t(language, "keyboard_language_vi"), callback_data="lang_vi"),
                InlineKeyboardButton(t(language, "keyboard_language_en"), callback_data="lang_en"),
            ],
            [InlineKeyboardButton(t(language, "keyboard_close_all"), callback_data="close_all")],
        ]
    )
