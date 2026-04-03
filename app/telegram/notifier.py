from __future__ import annotations

from typing import Optional


class TelegramNotifier:
    def __init__(self, application=None, chat_id: Optional[str] = None) -> None:
        self.application = application
        self.chat_id = chat_id

    async def send(self, message: str) -> None:
        if not self.application or not self.chat_id:
            return
        await self.application.bot.send_message(chat_id=self.chat_id, text=message)
