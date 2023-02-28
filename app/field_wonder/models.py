from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from app.base import DBBase
from app.store.database import db


class Question(DBBase):
    __tablename__ = 'question'

    description: sa_orm.Mapped[str]
    answer: sa_orm.Mapped[str]


class Round(DBBase):
    __tablename__ = 'round'

    player_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('player.id'))
    game: sa_orm.Mapped['Game'] = sa_orm.relationship(back_populates='round')
    finished: sa_orm.Mapped[datetime]

    player: sa_orm.Mapped['Player'] = sa_orm.relationship()


class Game(DBBase):
    __tablename__ = 'game'

    chat: sa_orm.Mapped[int]
    round_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('round.id'))
    question_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('question.id'))
    answered: sa_orm.Mapped[str]

    round: sa_orm.Mapped['Round'] = sa_orm.relationship(back_populates='game')
    question: sa_orm.Mapped['Question'] = sa_orm.relationship()
    players: sa_orm.Mapped[list["Player"]] = sa_orm.relationship(back_populates='game')


class Player(DBBase):
    __tablename__ = 'player'

    user_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('user.id'))
    game_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('game.id'))
    score: sa_orm.Mapped[int]
    fails: sa_orm.Mapped[bool]

    user: sa_orm.Mapped["User"] = sa_orm.relationship()
    game: sa_orm.Mapped["Game"] = sa_orm.relationship(back_populates="players")


class User(DBBase):
    __tablename__ = 'user'

    chat_id: sa_orm.Mapped[int] = sa_orm.mapped_column(unique=True)
    username: sa_orm.Mapped[str]


