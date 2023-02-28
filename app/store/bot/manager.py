import typing
from logging import getLogger

from app.store.vk_api.dataclasses import SendMessage, Updates

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Updates]):
        for update in updates:
            message = SendMessage(chat_id=update.message.chat.id, text=update.message.text)
            await self.app.store.vk_api.send_message(message)
