import asyncio
import random
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

                game = await self.app.store.field.create_game(user)
                all_users = await self.app.store.field.get_all_users()
                # all_users.remove(game)

                tasks = []
                for user in all_users:
                    task = self.app.store.tg_api.send_inline_button_poll(game=game, chat_id=user.chat_id)
                    tasks.append(task)

                result = asyncio.gather(*tasks)

            elif update.callback_query and update.callback_query.data.split("@")[0] == "poll_game":
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.callback_query.from_.id,
                                                                        username=update.callback_query.from_.username)
                game = await self.app.store.field.get_game_by_id(id_game=int(update.callback_query.data.split("@")[1]))

                # if any(map(lambda x: x.user_id == user.id, game.players)):
                if False:
                    message = SendMessage(chat_id=user.chat_id, text="Вы уже в игре")
                    await self.app.store.tg_api.send_message(message)
                else:
                    if len(game.players) + 1 >= 1:
                        await self.app.store.field.start_game(game)

                    else:
                        player = await self.app.store.field.create_player(user=user, game=game)
                        message = SendMessage(chat_id=user.chat_id, text=f"Вы в игре")
                        await self.app.store.tg_api.send_message(message)

            elif update.message and len(update.message.text) == 1:
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                        username=update.message.from_.username)
                player = await self.app.store.field.get_player_by_user(user)
                game = await self.app.store.field.get_game_by_id(player.game_id)

                if update.message.text in game.question.answer:
                    new_answered = ""
                    for v in game.question.answer:
                        if update.message.text == v:
                            new_answered += v
                        else:
                            new_answered += "-"

                    game.answered = new_answered
                    player.score += random.randint(0, 1000)
                    await self.app.store.field.update_data(game, player)
                else:
                    game.round.player_id = game.players[0]
                    await self.app.store.field.update_data(game)






