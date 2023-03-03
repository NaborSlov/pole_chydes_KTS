import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.field_wonder import Game, Player, UserTG, Round, Question


class FieldWonder(BaseAccessor):
    async def get_games(self) -> list[Game] | None:
        query = select(Game).options(selectinload(Game.players).selectinload(Player.user),
                                     selectinload(Game.question))

        async with self.app.database.session.begin() as session:
            rows = await session.scalars(query)
            result = rows.all()

        return result if result else None

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

    async def create_player(self, user_id: int) -> Player:
        async with self.app.database.session.begin() as session:
            player = Player(user_id=user_id)
            session.add(player)
            await session.commit()

        return player

    async def get_all_questions(self):
        async with self.app.database.session.begin() as session:
            rows = await session.scalars(select(Question))
            return rows.all()

    async def create_game(self, user: UserTG, poll_id: int) -> Game:
        player = await self.create_player(user.id)
        questions = await self.get_all_questions()
        question = random.choice(questions)
        async with self.app.database.session.begin() as session:
            round_game = Round()
            new_game = Game(poll_id=poll_id,
                            round=round_game,
                            question=question,
                            answered="-" * len(question.answer),
                            players=[player])

            session.add(new_game)

            await session.commit()

        return new_game

    async def add_player_in_game(self, user, poll_id: int):
        async with self.app.database.session.begin() as session:
            game = await session.scalar(
                select(Game).options(selectinload(Game.players).selectinload(Player.user)).where(
                    Game.poll_id == poll_id))

            for player in game.players:
                if player.user.chat_id == user.chat_id:
                    return None

            player = Player(user=user, game=game)
            session.add(player)
            await session.commit()
