from __future__ import annotations

import asyncio
from typing import Optional

from telegram import Bot


class TelegramNotifier:
    def __init__(self, application=None, chat_id: Optional[str] = None, token: Optional[str] = None) -> None:
        self.application = application
        self.chat_id = chat_id
        self.token = token
        self._bot: Bot | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _bot_for_current_loop(self) -> Bot | None:
        if not self.token:
            return None
        loop = asyncio.get_running_loop()
        if self._bot is None or self._loop is not loop:
            self._bot = Bot(token=self.token)
            self._loop = loop
        return self._bot

    async def send(self, message: str) -> None:
        if not self.chat_id:
            return
        bot = self._bot_for_current_loop()
        if bot is not None:
            await bot.send_message(chat_id=self.chat_id, text=message)
            return
        if self.application:
            await self.application.bot.send_message(chat_id=self.chat_id, text=message)
