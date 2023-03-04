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

    async def create_player(self, user: UserTG, game: Game) -> Player:
        async with self.app.database.session.begin() as session:
            player = Player(user=user, game=game)
            session.add(player)
            await session.commit()

        return player

    async def get_game_by_poll_id(self, poll_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            game = await session.scalar(select(Game).options(selectinload(Game.players),
                                                             selectinload(Game.question),
                                                             selectinload(Game.round)).where(Game.poll_id == poll_id))
            return game

    async def get_all_questions(self):
        async with self.app.database.session.begin() as session:
            rows = await session.scalars(select(Question))
            return rows.all()

    async def create_game(self, user: UserTG, poll_id: int) -> None:
        questions = await self.get_all_questions()
        question = random.choice(questions)
        async with self.app.database.session.begin() as session:
            player = Player(user=user)
            round_game = Round()
            new_game = Game(poll_id=poll_id,
                            round=round_game,
                            question=question,
                            answered="-" * len(question.answer),
                            players=[player])

            session.add(new_game)

            await session.commit()
