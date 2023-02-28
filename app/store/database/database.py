import typing

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.store.database.sqlalchemy_base import db

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: AsyncEngine | None = None
        self._db: declarative_base | None = None
        self.session: async_sessionmaker | None = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        self._engine = create_async_engine(self.app.config.database.url_database, echo=True)
        self.session = async_sessionmaker(self._engine, expire_on_commit=False)

    async def disconnect(self, *_: list, **__: dict) -> None:
        if self._engine:
            await self._engine.dispose()
