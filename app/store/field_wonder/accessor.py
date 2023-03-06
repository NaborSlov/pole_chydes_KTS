import asyncio
import datetime
import random

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.field_wonder import Game, Player, UserTG, Round, Question
from app.store.vk_api.dataclasses import SendMessage


class FieldWonder(BaseAccessor):
    async def get_games(self) -> list[Game] | None:
        query = select(Game).options(selectinload(Game.players).selectinload(Player.user),
                                     selectinload(Game.question))

        async with self.app.database.session.begin() as session:
            rows = await session.scalars(query)
            result = rows.all()

        return result if result else None

    async def get_all_users(self) -> list[UserTG] | list:
        async with self.app.database.session.begin() as session:
            row = await session.scalars(select(UserTG))
            users = row.all()

            return users if users else []

    async def get_or_create_user_tg(self, chat_id: int, username: str) -> UserTG:
        query = select(UserTG).where(UserTG.chat_id == chat_id,
                                     UserTG.username == username)

        async with self.app.database.session.begin() as session:
            row = await session.scalar(query)

            if row:
                return row

            new_user = UserTG(chat_id=chat_id, username=username)
            session.add(new_user)
            await session.commit()

        return new_user

    async def create_player(self, user: UserTG, game: Game) -> Player:
        async with self.app.database.session.begin() as session:
            player = Player(user=user, game=game)
            session.add(player)
            await session.commit()

        return player

    async def get_game_by_id(self, id_game: int) -> Game:
        query = select(Game).options(selectinload(Game.players).selectinload(Player.user),
                                     selectinload(Game.question),
                                     selectinload(Game.round).selectinload(
                                         Round.player).selectinload(Player.user)).where(
            Game.id == id_game)

        async with self.app.database.session.begin() as session:
            game = await session.scalar(query)
            return game

    async def get_all_questions(self):
        async with self.app.database.session.begin() as session:
            rows = await session.scalars(select(Question))
            return rows.all()

    async def create_game(self, user: UserTG) -> Game:
        questions = await self.get_all_questions()
        question = random.choice(questions)
        async with self.app.database.session.begin() as session:
            player = Player(user=user)
            round_game = Round()
            new_game = Game(round=round_game,
                            question=question,
                            answered="-" * len(question.answer),
                            players=[player])

            session.add(new_game)

            await session.commit()

        return new_game

    async def start_game(self, game) -> Game:
        async with self.app.database.session.begin() as session:
            if game.started:
                return game

            player = random.choice(game.players)
            await session.scalar(update(Round).where(Round.id == game.round_id).values(
                player_id=player.id,
                finished=datetime.datetime.now() + datetime.timedelta(minutes=5)
            ))

            game = await session.scalar(
                update(Game).where(Game.id == game.id).values(started=True).returning(Game).options(
                    selectinload(Game.players).selectinload(Player.user),
                    selectinload(Game.question),
                    selectinload(Game.round).selectinload(
                        Round.player).selectinload(Player.user)))
            await session.commit()
            return game

    async def get_player_by_user(self, user: UserTG):
        query = select(Player).where(Player.user_id == user.id)
        async with self.app.database.session.begin() as session:
            row = await session.scalars(query)
            return row.all()

    async def update_data(self, model):
        async with self.app.database.session.begin() as session:
            session.add(model)
            await session.commit()
