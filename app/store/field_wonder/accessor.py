from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.base.base_accessor import BaseAccessor
from app.field_wonder import Game, Player, UserTG


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


