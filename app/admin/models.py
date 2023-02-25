import sqlalchemy as sa

from app.store.database import db


class AdminModel(db):
    __tablename__ = "admins"

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String, nullable=False, unique=True)
    password = sa.Column(sa.VARCHAR(255), nullable=False)
