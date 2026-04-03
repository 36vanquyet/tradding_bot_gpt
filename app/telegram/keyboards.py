from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Status", callback_data="status"),
                InlineKeyboardButton("Health", callback_data="health"),
            ],
            [
                InlineKeyboardButton("Auto ON", callback_data="auto_on"),
                InlineKeyboardButton("Auto OFF", callback_data="auto_off"),
            ],
            [
                InlineKeyboardButton("Pause", callback_data="pause"),
                InlineKeyboardButton("Resume", callback_data="resume"),
            ],
            [
                InlineKeyboardButton("Mode: Paper", callback_data="mode_paper"),
                InlineKeyboardButton("Mode: Live", callback_data="mode_live"),
            ],
            [InlineKeyboardButton("Close All", callback_data="close_all")],
        ]
    )
