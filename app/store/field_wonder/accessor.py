from sqlalchemy import select
from sqlalchemy.orm import selectinload, lazyload

from app.base.base_accessor import BaseAccessor
from app.field_wonder import Game, Player


class FieldWonder(BaseAccessor):
    async def get_games(self) -> list[Game] | None:
        query = select(Game).options(selectinload(Game.players).selectinload(Player.user),
                                     selectinload(Game.question))

        async with self.app.database.session.begin() as session:
            rows = await session.scalars(query)
            result = rows.all()

        return result if result else None
