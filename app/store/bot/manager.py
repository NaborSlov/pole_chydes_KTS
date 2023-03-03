import asyncio
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
                await self.app.store.tg_api.send_inline_button_start(user)

            elif update.callback_query and update.callback_query.data == "/create_poll":
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.callback_query.from_.id,
                                                                        username=update.callback_query.from_.username)
                poll_id = await self.app.store.tg_api.send_poll_start(user)
                await self.app.store.field.create_game(user, int(poll_id))

            elif update.poll_answer and update.poll_answer.option_ids[0] == 0:
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.poll_answer.user.id,
                                                                        username=update.poll_answer.user.username)
                await self.app.store.field.add_player_in_game(user, poll_id=update.poll_answer.poll_id)

                message = SendMessage(chat_id=user.chat_id, text="Вы в игре")
                await self.app.store.tg_api.send_message(message)


