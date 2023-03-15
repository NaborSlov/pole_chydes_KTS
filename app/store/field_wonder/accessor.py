import datetime
import random
from typing import Optional, Union

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.field_wonder import Game, Player, UserTG, Round, Question


class FieldWonder(BaseAccessor):
    async def get_games(self) -> Optional[list[Game]]:
        query = select(Game).options(selectinload(Game.players).selectinload(Player.user),
                                     selectinload(Game.question))

        async with self.app.database.session.begin() as session:
            rows = await session.scalars(query)
            result = rows.all()

        return result or None

    async def get_all_users(self) -> Union[list[UserTG], list]:
        async with self.app.database.session.begin() as session:
            row = await session.scalars(select(UserTG))
            users = row.all()

            return users or []

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
                            owner_name=user.username,
                            question=question,
                            answered="_" * len(question.answer),
                            players=[player])

            session.add(new_game)

            await session.commit()

        return new_game

    async def start_game(self, game) -> Game:
        async with self.app.database.session.begin() as session:
            if game.started:
                return game

            player = random.choice(game.players)
            await session.execute(update(Round).where(Round.id == game.round_id).values(
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

    async def exit_player_game(self, game: Game, player: Player):
        async with self.app.database.session.begin() as session:
            await session.execute(update(Round).where(Round.game == game).values(player_id=None))
            await session.flush()
            await session.execute(delete(Player).where(Player.id == player.id))
            await session.commit()

    async def get_all_rounds(self) -> Union[list[Round], list]:
        async with self.app.database.session.begin() as session:
            result = await session.scalars(select(Round).options(selectinload(Round.game),
                                                                 selectinload(Round.player).selectinload(Player.user)))
            result = [item for item in result.all() if item.game.started is True]

        return result or []
