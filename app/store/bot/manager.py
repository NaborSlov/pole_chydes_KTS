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

            if update.message and update.message.text == "/start":
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                        username=update.message.from_.username)
                await self.app.store.tg_api.send_inline_button_start(user.chat_id)
            elif update.callback_query and update.callback_query.data == "/create_poll":
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.callback_query.from_.id,
                                                                        username=update.callback_query.from_.username)
                await self.app.store.tg_api.send_poll_start(user.chat_id)


