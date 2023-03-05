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

            if update.message:
                if update.message.text == "/start":
                    user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                            username=update.message.from_.username)
                    await self.app.store.tg_api.send_inline_button_start(user)

                elif update.message.text == "/exit":  # выход из игровой сессии
                    ...

                else:  # ответ на вопрос
                    user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                            username=update.message.from_.username)
                    players = await self.app.store.field.get_player_by_user(user)

                    for player in players:
                        game = await self.app.store.field.get_game_by_id(player.game_id)

                        if game.round.player_id == player.id and game.started and player.fails:

                            if len(update.message.text) == 1 and update.message.text in game.question.answer:  # Одна буква

                                new_answered = "".join(
                                    list(map(lambda x: x if x == update.message.text else "-",
                                             game.question.answer)))
                                game.answered = new_answered
                                score = random.randint(0, 1000)
                                player.score += score
                                await self.app.store.field.update_data(player)
                                await self.app.store.field.update_data(game)

                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Вы угадали и получили {score} очков\n"
                                                           f"Опять ваш ход")
                                await self.app.store.tg_api.send_message(message)

                                messages_answer = []
                                for player in game.players:
                                    messages_answer.append(
                                        SendMessage(chat_id=player.user.chat_id,
                                                    text=f"Теперь ответ:{game.answered}"))

                                await asyncio.gather(*messages_answer)

                            elif len(update.message.text) == 1:  # Неправильная буква
                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Вы не угадали")
                                await self.app.store.tg_api.send_message(message)

                                try:
                                    next_player = next(
                                        filter(lambda x: x.id != game.round.player_id, game.players))
                                    game.round.player_id = next_player.id
                                    await self.app.store.field.update_data(game)
                                    message = SendMessage(chat_id=next_player.chat_id, text="Ваш ход")
                                    await self.app.store.tg_api.send_message(message)
                                except StopIteration:
                                    message = SendMessage(chat_id=user.chat_id, text="Ваш ход")
                                    await self.app.store.tg_api.send_message(message)

                            elif update.message.text == game.question.answer:  # Все слово
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы победили")
                                await self.app.store.tg_api.send_message(message)
                                game.started = False
                                await self.app.store.field.update_data(game)

                            elif len(update.message.text) != len(
                                    game.answered):  # Неправильное количество букв в ответе
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы опечатались?\nВаш ход!")
                                await self.app.store.tg_api.send_message(message)

                            else:  # Слово не правильное
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Не правильное слово\nВы выбыли из игры")
                                await self.app.store.tg_api.send_message(message)

                                next_player = next(
                                    filter(lambda x: x.id != game.round.player_id, game.players))
                                game.round.player_id = next_player.id

                                message = SendMessage(chat_id=next_player.chat_id, text="Ваш ход")
                                await self.app.store.tg_api.send_message(message)

                                player.fails = True

                                await self.app.store.field.update_data(game, player)

                        elif game.started:  # Сейчас не твой ход
                            ...

            if update.callback_query:
                if update.callback_query.data == "/create_poll":  # создания опроса
                    user = await self.app.store.field.get_or_create_user_tg(
                        chat_id=update.callback_query.from_.id,
                        username=update.callback_query.from_.username)

                    game = await self.app.store.field.create_game(user)
                    all_users = await self.app.store.field.get_all_users()
                    # all_users.remove(user)

                    tasks = []
                    for user in all_users:
                        task = self.app.store.tg_api.send_inline_button_poll(game=game,
                                                                             chat_id=user.chat_id)
                        tasks.append(task)

                    result = asyncio.gather(*tasks)

                elif update.callback_query.data.split("@")[0] == "poll_game":  # обработка ответа
                    user = await self.app.store.field.get_or_create_user_tg(
                        chat_id=update.callback_query.from_.id,
                        username=update.callback_query.from_.username)
                    game = await self.app.store.field.get_game_by_id(
                        id_game=int(update.callback_query.data.split("@")[1]))

                    # if any(map(lambda x: x.user_id == user.id, game.players)):
                    if False:  # Если игрок уже в игре
                        message = SendMessage(chat_id=user.chat_id, text="Вы уже в игре")
                        await self.app.store.tg_api.send_message(message)
                    else:  # Игроки собраны
                        if len(game.players) + 1 >= 1:
                            await self.app.store.field.start_game(game)

                        else:  # Игрок добавлен
                            player = await self.app.store.field.create_player(user=user, game=game)
                            message = SendMessage(chat_id=user.chat_id, text=f"Вы в игре")
                            await self.app.store.tg_api.send_message(message)
