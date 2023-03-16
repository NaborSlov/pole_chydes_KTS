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
        message_question = f"Вопрос:{game.question.description}"
        await self.send_message_players_in_game(game=game, text=message_question)

        message_answer = f"Открытые буквы: {game.answered}"
        await self.send_message_players_in_game(game=game, text=message_answer)

    async def next_player(self, game: Game):
        """
        Передача хода следующему игроку
        """
        players_in_game = list(filter(lambda x: x.fails, game.players))

        if len(players_in_game) <= 1:
            next_player = players_in_game[0]
        else:
            player_index = players_in_game.index(game.round.player)
            players_in_game = players_in_game[player_index:] + players_in_game[:player_index]
            next_player = players_in_game[1]

        game.round.player_id = next_player.id
        game.round.finished = datetime.datetime.now() + datetime.timedelta(minutes=2)
        await self.app.store.field.update_data(game)

        message = f"Сейчас ход: {next_player.user.username}"
        await self.send_message_players_in_game(game=game, text=message)

        await self.send_questions_and_answered(game=game)

        await self.app.store.tg_api.send_you_turn(chat_id=next_player.user.chat_id, game=game)

    async def end_game_and_statistics(self, game: Game):
        """
        Закрывает игру и отправляет по ней статистику
        """
        game.started = False
        await self.app.store.field.update_data(game)
        game = await self.app.store.field.get_game_by_id(id_game=game.id)

        message = f"Игра завершена, статистика по игре:"
        await self.send_message_players_in_game(game=game, text=message)

        for player in game.players:
            message = f"{player.user.username}: {player.score}"
            await self.send_message_players_in_game(game=game, text=message)

    async def send_winner(self, game: Game, user: UserTG):
        """
        Отправляет всем участникам игры имя победителя
        """
        message_winner = f"Победитель: {user.username}"
        await self.send_message_players_in_game(game=game, text=message_winner)

    async def send_inline_keyboard_start(self, users: list[UserTG], game: Game):
        """
        Отправляет стартовую кнопку всем пользователям бота
        """
        tasks = []
        for user in users:
            task = self.app.store.tg_api.send_inline_button_poll(game=game,
                                                                 chat_id=user.chat_id,
                                                                 username=game.owner_name)
            tasks.append(task)

        results = asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                self.logger.exception("send_button_start", exc_info=result)

    async def send_message_players_in_game(self, game: Game, text: str):
        """
        Отправляет сообщение всем игрокам в игре
        """
        tasks = []
        for player in game.players:
            message = SendMessage(chat_id=player.user.chat_id, text=text)
            task = self.app.store.tg_api.send_message(message)
            tasks.append(task)

        results = asyncio.gather(*tasks, return_exceptions=True)
        if isinstance(results, list):
            for result in results:
                if isinstance(result, Exception):
                    self.logger.exception("send_all_players", exc_info=result)
        else:
            if isinstance(results, Exception):
                self.logger.exception("send_all_players", exc_info=results)

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
                result += "*"

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
        rounds = await self.app.store.field.get_all_rounds()
        for round_game in rounds:
            if not round_game.player:
                continue

            if round_game.finished < datetime.datetime.now():
                game = await self.app.store.field.get_game_by_id(id_game=round_game.game.id)
                await self.app.store.field.exit_player_game(player=round_game.player)
                await self.next_player(game=game)

                message = f"Игрок {round_game.player.user.username} вышел из игры: {game.owner_name}"
                await self.send_message_players_in_game(game=game, text=message)

    async def start_game(self, game: Game):
        game = await self.app.store.field.start_game(game=game)

        message_start = f"Игра игрока {game.owner_name} началась"
        await self.send_message_players_in_game(game=game, text=message_start)

        message_turn = f"Сейчас ход {game.round.player.user.username}"
        await self.send_message_players_in_game(game=game, text=message_turn)

        await self.send_questions_and_answered(game=game)
        await self.app.store.tg_api.send_you_turn(game=game, chat_id=game.round.player.user.chat_id)

    async def handle_updates(self, updates: list[Updates]):
        await self.check_user_waiting()

        for update in updates:

            if update.message:
                user = await self.app.store.field.get_or_create_user_tg(chat_id=update.message.from_.id,
                                                                        username=update.message.from_.username)
                if update.message.text == "/start":
                    message = SendMessage(chat_id=user.chat_id,
                                          text="""
                                          Вы начали игровую сессию,                              
                                          теперь вы можете получать приглашения от других игроков 
                                          , если вы не хотите больше получать сообщения, 
                                          нажмите на "Выход из игры".
                                          """)
                    await self.app.store.tg_api.send_message(message=message)

                elif update.message.text == "/new_game":
                    await self.app.store.tg_api.send_inline_button_create_game(user)

                elif update.message.text == "/exit_game":
                    await self.app.store.field.del_user(user)
                    message = SendMessage(chat_id=user.chat_id,
                                          text="""
                                          Вы вышли из игровой сессии,                              
                                          если вы хотите получать приглашения в            
                                          игры, нажмите на "Начать игру".
                                          """)
                    await self.app.store.tg_api.send_message(message=message)

                else:  # ответ на вопрос
                    players = await self.app.store.field.get_players_by_user(user)

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
                                    await self.send_winner(game=game, user=user)
                                    await self.end_game_and_statistics(game)
                                else:
                                    message = f"Игрок {user.username} правильно назвал букву и получил {score} очков."
                                    await self.send_message_players_in_game(game=game, text=message)
                                    await self.send_questions_and_answered(game=game)
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
                                score = random.randrange(0, 1000, 100)
                                player.score += score
                                await self.app.store.field.update_data(player)

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
                    all_users = list(filter(lambda x: x.chat_id != user.chat_id, all_users))

                    await self.app.store.tg_api.send_inline_button_start(user=user, game=game)
                    await self.send_inline_keyboard_start(all_users, game)

                elif update.callback_query.data.split("@")[0] == "just_start_game":  # начать игру немедленно
                    game = await self.app.store.field.get_game_by_id(
                        id_game=int(update.callback_query.data.split("@")[1]))
                    await self.start_game(game=game)

                elif update.callback_query.data.split("@")[0] == "poll_game":  # обработка ответа от пользователя
                    game = await self.app.store.field.get_game_by_id(
                        id_game=int(update.callback_query.data.split("@")[1]))

                    if any(map(lambda x: x.user_id == user.id, game.players)):  # Если игрок уже в игре
                        message = SendMessage(chat_id=user.chat_id, text=f"Вы уже в игре {game.owner_name}")
                        await self.app.store.tg_api.send_message(message)
                    else:
                        if len(game.players) + 1 >= 3:  # Все игроки собранны, начало игры
                            await self.start_game(game=game)

                        else:  # Игрок добавлен
                            await self.app.store.field.create_player(user=user, game=game)
                            message = SendMessage(chat_id=user.chat_id, text=f"Вы добавлены в игру {game.owner_name}")
                            await self.app.store.tg_api.send_message(message)

                            text = f"{len(game.players)}/3 в игре {game.owner_name}"
                            await self.send_message_players_in_game(game, text=text)

                elif update.callback_query.data.split("@")[0] == "exit_game":  # выход из игры
                    game = await self.app.store.field.get_game_by_id(int(update.callback_query.data.split("@")[1]))
                    player = next(filter(lambda x: x.user_id == user.id, game.players))

                    if len(game.players) > 1:
                        await self.next_player(game)

                    await self.app.store.field.exit_player_game(player)

                    message = f"Игрок {user.username} вышел из игры: {game.owner_name}"
                    await self.send_message_players_in_game(game=game, text=message)
