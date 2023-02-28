from sqlalchemy.orm import Mapped, mapped_column

from app.store.database import db


class DBBase(db):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
