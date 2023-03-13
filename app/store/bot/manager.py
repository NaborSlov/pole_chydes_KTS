import asyncio
import datetime
import random
import typing
from logging import getLogger

from app.field_wonder import Game, UserTG, Player
from app.store.vk_api.dataclasses import SendMessage, Updates

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def send_questions_and_answered(self, game: Game):
        """
        Отправка вопроса и уже отвеченных букв всем участникам игры
        """
        messages_question = []
        for player in game.players:
            messages_question.append(
                SendMessage(chat_id=player.user.chat_id, text=f"Вопрос:{game.question.description}"))

        messages_answer = []
        for player in game.players:
            messages_answer.append(
                SendMessage(chat_id=player.user.chat_id, text=f"Отвечено: {game.answered}"))

        res_quests = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_question])
        res_answer = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_answer])

        for res_q, res_a in zip(res_quests, res_answer):
            if isinstance(res_a, Exception):
                self.logger.exception('send_question', exc_info=res_a)

            if isinstance(res_q, Exception):
                self.logger.exception('send_answered', exc_info=res_q)

    async def next_player(self, game: Game):
        """
        Передача хода следующему игроку
        """
        players_in_game = list(filter(lambda x: x.fails, game.players))
        player_index = players_in_game.index(game.round.player)

        if len(players_in_game) == 1 or player_index + 1 > len(players_in_game) - 1:
            next_player = players_in_game[0]
        else:
            next_player = players_in_game[player_index + 1]

        game.round.player_id = next_player.id
        game.round.finished = datetime.datetime.now() + datetime.timedelta(minutes=2)
        await self.app.store.field.update_data(game)
        await self.app.store.tg_api.send_you_turn(chat_id=next_player.user.chat_id, game=game)

    async def end_game_and_statistics(self, game: Game):
        """
        Закрывает игру и отправляет по ней статистику
        """
        game.started = False
        await self.app.store.field.update_data(game)

        messages_score = []
        for player in game.players:
            messages_score.append(
                SendMessage(chat_id=player.user.chat_id, text=f"{player.user.username}: {player.score}"))

        res_answer = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_score], return_exceptions=True)

        for result in res_answer:
            if isinstance(result, Exception):
                self.logger.exception("send_statistic", exc_info=result)

    async def send_winner(self, game: Game, user: UserTG):
        """
        Отправляет всем участникам игры имя победителя
        """
        messages_winner = []
        for player in game.players:
            messages_winner.append(
                SendMessage(chat_id=player.user.chat_id, text=f"Победитель: {user.username}"))

        res_answer = await asyncio.gather(
            *[self.app.store.tg_api.send_message(message) for message in messages_winner], return_exceptions=True)

        for result in res_answer:
            if isinstance(result, Exception):
                self.logger.exception("send_winner", exc_info=result)

    async def send_inline_keyboard_start(self, users: list[UserTG], game: Game):
        """
        Отправляет стартовую кнопку всем пользователям бота
        """
        tasks = []
        for user in users:
            task = self.app.store.tg_api.send_inline_button_poll(game=game,
                                                                 chat_id=user.chat_id)
            tasks.append(task)

        results = asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                self.logger.exception("send_button_start", exc_info=result)

    @staticmethod
    def _new_answered(game: Game, letter_ans: str) -> str:
        """
        Составляет новый ответ и возвращает его
        """
        result = ""
        for let in game.question.answer:
            if letter_ans == let and let not in game.answered:
                result += let
            elif let in game.answered:
                result += let
            else:
                result += "_"

        return result

    @staticmethod
    def _get_win_player(players: list[Player]) -> Player:
        """
        Определяет игрока с самым большим количеством очков
        """
        max_score = 0
        player_win = None
        for player in players:
            if max_score < player.score:
                max_score = player.score
                player_win = player

        return player_win

    async def check_user_waiting(self):
        rounds = self.app.store.field.get_all_rounds()
        for round_game in rounds:
            if round_game.finished < datetime.datetime.now():
                game = await self.app.store.field.get_game_by_id(id_game=round_game.game.id)
                await self.app.store.field.exit_player_game(game=game, user=round_game.player.user)
                await self.next_player(game=game)

                message = SendMessage(chat_id=round_game.player.user.chat_id, text="Вы вышли из игры.")
                await self.app.store.tg_api.send_message(message)

    async def handle_updates(self, updates: list[Updates]):
        await self.check_user_waiting()

        for update in updates:

            if update.message:
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                        username=update.message.from_.username)
                if update.message.text == "/start":
                    await self.app.store.tg_api.send_inline_button_start(user)

                else:  # ответ на вопрос
                    players = await self.app.store.field.get_player_by_user(user)

                    for player in players:
                        game = await self.app.store.field.get_game_by_id(player.game_id)

                        if game.round.player_id == player.id and game.started and player.fails:

                            if len(update.message.text) == 1 \
                                    and update.message.text in game.question.answer \
                                    and update.message.text not in game.answered:  # Одна буква

                                new_answered = self._new_answered(game, update.message.text)
                                game.answered = new_answered

                                score = random.randrange(0, 1000, 100)
                                player.score += score

                                await self.app.store.field.update_data(player)
                                await self.app.store.field.update_data(game)

                                if game.question.answer == new_answered:
                                    await self.end_game_and_statistics(game)
                                else:
                                    message = SendMessage(chat_id=user.chat_id,
                                                          text=f"Вы угадали и получили {score} очков.")
                                    await self.app.store.tg_api.send_message(message)
                                    await self.app.store.tg_api.send_you_turn(chat_id=user.chat_id, game=game)

                            elif len(update.message.text) == 1 \
                                    and update.message.text in game.answered:  # Такая буква уже была
                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Эта буква уже была.")
                                await self.app.store.tg_api.send_message(message)
                                await self.next_player(game)

                            elif len(update.message.text) == 1 \
                                    and update.message.text not in game.question.answer:  # Неправильная буква
                                message = SendMessage(chat_id=user.chat_id,
                                                      text=f"Такой буквы нет.")
                                await self.app.store.tg_api.send_message(message)
                                await self.next_player(game)

                            elif update.message.text == game.question.answer:  # Все слово правильное
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы победили.")
                                await self.app.store.tg_api.send_message(message)
                                await self.send_winner(game=game, user=user)
                                await self.end_game_and_statistics(game)

                            elif len(update.message.text) != len(
                                    game.answered):  # Неправильное количество букв в ответе
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Вы опечатались?")
                                await self.app.store.tg_api.send_message(message)
                                await self.app.store.tg_api.send_you_turn(chat_id=user.chat_id, game=game)

                            else:  # Слово не правильное
                                message = SendMessage(chat_id=user.chat_id,
                                                      text="Не правильное слово, вы выбыли из игры.")
                                await self.app.store.tg_api.send_message(message)

                                players_in_game = list(map(lambda x: x.fails, game.players))
                                if len(players_in_game) <= 1:
                                    player_win = self._get_win_player(game.players)
                                    await self.send_winner(game, player_win.user)
                                    await self.end_game_and_statistics(game)

                                else:
                                    player.fails = False
                                    await self.app.store.field.update_data(player)
                                    await self.next_player(game)

            if update.callback_query:
                user = await self.app.store.field.get_or_create_user_tg(
                    chat_id=update.callback_query.from_.id,
                    username=update.callback_query.from_.username)

                if update.callback_query.data.split("@")[0] == "create_poll":  # создания опроса
                    game = await self.app.store.field.create_game(user)
                    all_users = await self.app.store.field.get_all_users()
                    # all_users.remove(user)  # TODO не забыть вернуть
                    await self.send_inline_keyboard_start(all_users, game)

                elif update.callback_query.data.split("@")[0] == "poll_game":  # обработка ответа от пользователя
                    game = await self.app.store.field.get_game_by_id(
                        id_game=int(update.callback_query.data.split("@")[1]))

                    if any(map(lambda x: x.user_id == user.id, game.players)):  # Если игрок уже в игре
                        message = SendMessage(chat_id=user.chat_id, text="Вы уже в этой игре.")
                        await self.app.store.tg_api.send_message(message)
                    else:
                        # if len(game.players) + 1 >= 3:  # TODO не забыть вернуть # Игроки собраны
                        if len(game.players) + 1 >= 2:
                            game = await self.app.store.field.start_game(game)
                            await self.send_questions_and_answered(game)

                            message = SendMessage(chat_id=game.round.player.user.chat_id,
                                                  text="Ваш ход.")
                            await self.app.store.tg_api.send_message(message)

                        else:  # Игрок добавлен
                            await self.app.store.field.create_player(user=user, game=game)
                            message = SendMessage(chat_id=user.chat_id, text=f"Вы добавлены в игру.")
                            await self.app.store.tg_api.send_message(message)

                elif update.callback_query.data.split("@")[0] == "exit_game":  # выход из игры
                    game = await self.app.store.field.get_game_by_id(int(update.callback_query.data.split("@")[1]))
                    if len(game.players) > 1:
                        await self.next_player(game)

                    await self.app.store.field.exit_player_game(game, user)

                    message = SendMessage(chat_id=user.chat_id, text="Вы вышли из игры.")
                    await self.app.store.tg_api.send_message(message)
