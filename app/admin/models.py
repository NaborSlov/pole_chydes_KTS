from hashlib import sha256

import sqlalchemy as sa
from aiohttp_session import Session

from app.base import DBBase


class AdminModel(DBBase):
    __tablename__ = "admins"

    username = sa.Column(sa.String, nullable=False, unique=True)
    password = sa.Column(sa.VARCHAR(255), nullable=False)

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Session | None) -> "AdminModel":
        return cls(id=session["admin"]["id"], email=session["admin"]["username"])

