import asyncio
import random
import typing
from logging import getLogger

from app.field_wonder import Game
from app.store.vk_api.dataclasses import SendMessage, Updates

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def send_questions_and_answered(self, game: Game):
        messages_question = []
        for player in game.players:
            messages_question.append(
                SendMessage(chat_id=player.user.chat_id, text=f"Вопрос:{game.question.description}"))

        messages_answer = []
        for player in game.players:
            messages_answer.append(
                SendMessage(chat_id=player.user.chat_id, text=f"Ответ:{game.answered}"))

        res_quests = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_question])
        res_answer = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_answer])

        await self.app.store.bots_manager.send_questions_and_answered(game)

        message = SendMessage(chat_id=game.round.player.user.chat_id, text="Ваш ход")
        await self.app.store.tg_api.send_message(message)

    async def next_player(self, game: Game):
        players_in_game = list(map(lambda x: x.fails, game.players))

        if len(players_in_game) == 1 or players_in_game.index(game.round.player) + 1 > len(players_in_game):
            next_player = players_in_game[0]
        else:
            next_player = players_in_game[players_in_game.index(game.round.player) + 1]

        game.round.player_id = next_player.id
        await self.app.store.field.update_data(game)
        message = SendMessage(chat_id=next_player.chat_id, text="Ваш ход")
        await self.app.store.tg_api.send_message(message)

    async def end_game_and_statistics(self, game: Game):
        game.started = False
        await self.app.store.field.update_data(game)

    async def handle_updates(self, updates: list[Updates]):
        for update in updates:

            if update.message:
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                        username=update.message.from_.username)
                if update.message.text == "/start":
                    await self.app.store.tg_api.send_inline_button_start(user)

                elif update.message.text == "/exit":  # выход из игровой сессии
                    ...

                else:  # ответ на вопрос
                    players = await self.app.store.field.get_player_by_user(user)

                    for player in players:
                        game = await self.app.store.field.get_game_by_id(player.game_id)

                        if game.round.player_id == player.id and game.started and player.fails:

                            if len(update.message.text) == 1 and update.message.text in game.question.answer:  # Одна буква

                                new_answered = ''

                                game.answered = new_answered
                                score = random.randint(0, 1000)
                                player.score += score
                                await self.app.store.field.update_data(player)
                                await self.app.store.field.update_data(game)

                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Вы угадали и получили {score} очков\n"
                                                           f"Опять ваш ход")
                                await self.app.store.tg_api.send_message(message)
                                await self.app.store.tg_api.send_questions_and_answered(game)

                            elif len(update.message.text) == 1:  # Неправильная буква
                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Вы не угадали")
                                await self.app.store.tg_api.send_message(message)
                                await self.app.store.field.next_player(game)

                            elif update.message.text == game.question.answer:  # Все слово правильное
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы победили")
                                await self.app.store.tg_api.send_message(message)
                                await self.end_game_and_statistics(game)

                            elif len(update.message.text) != len(
                                    game.answered):  # Неправильное количество букв в ответе
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы опечатались?\nВаш ход!")
                                await self.app.store.tg_api.send_message(message)

                            else:  # Слово не правильное
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Не правильное слово\nВы выбыли из игры")
                                await self.app.store.tg_api.send_message(message)

                                players_in_game = list(map(lambda x: x.fails, game.players))
                                if len(players_in_game) <= 1:
                                    await self.end_game_and_statistics(game)
                                else:
                                    player.fails = False
                                    await self.app.store.field.update_data(player)
                                    await self.next_player(game)

                        elif game.started:  # Сейчас не твой ход
                            ...

            if update.callback_query:
                user = await self.app.store.field.get_or_create_user_tg(
                    chat_id=update.callback_query.from_.id,
                    username=update.callback_query.from_.username)

                if update.callback_query.data == "/create_poll":  # создания опроса

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
                    game = await self.app.store.field.get_game_by_id(
                        id_game=int(update.callback_query.data.split("@")[1]))

                    # if any(map(lambda x: x.user_id == user.id, game.players)):  # Если игрок уже в игре
                    if False:  # TODO не забыть убрать
                        message = SendMessage(chat_id=user.chat_id, text="Вы уже в игре")
                        await self.app.store.tg_api.send_message(message)
                    else:  # Игроки собраны
                        # if len(game.players) + 1 >= 3:  # TODO не забыть вернуть
                        if len(game.players) + 1 >= 1:
                            game = await self.app.store.field.start_game(game)
                            await send_questions_and_answered(game)

                        else:  # Игрок добавлен
                            player = await self.app.store.field.create_player(user=user, game=game)
                            message = SendMessage(chat_id=user.chat_id, text=f"Вы в игре")
                            await self.app.store.tg_api.send_message(message)
