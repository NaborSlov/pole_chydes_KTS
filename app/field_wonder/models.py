from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from app.base import DBBase


class Question(DBBase):
    __tablename__ = 'question'

    description: sa_orm.Mapped[str]
    answer: sa_orm.Mapped[str]


class Round(DBBase):
    __tablename__ = 'round'

    player_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('player.id'), nullable=True)
    finished: sa_orm.Mapped[datetime] = sa_orm.mapped_column(nullable=True)

    game: sa_orm.Mapped['Game'] = sa_orm.relationship(back_populates='round')
    player: sa_orm.Mapped['Player'] = sa_orm.relationship()


class Game(DBBase):
    __tablename__ = 'game'

    round_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('round.id'), nullable=True)
    question_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('question.id'), nullable=True)
    answered: sa_orm.Mapped[str]
    started: sa_orm.Mapped[bool] = sa_orm.mapped_column(default=False)

    round: sa_orm.Mapped['Round'] = sa_orm.relationship(back_populates='game')
    question: sa_orm.Mapped['Question'] = sa_orm.relationship()
    players: sa_orm.Mapped[list["Player"]] = sa_orm.relationship(back_populates='game')


class Player(DBBase):
    __tablename__ = 'player'

    user_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('user_tg.id'), nullable=True)
    game_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('game.id'), nullable=True)
    score: sa_orm.Mapped[int] = sa_orm.mapped_column(default=0)
    fails: sa_orm.Mapped[bool] = sa_orm.mapped_column(default=False)

    user: sa_orm.Mapped["UserTG"] = sa_orm.relationship()
    game: sa_orm.Mapped["Game"] = sa_orm.relationship(back_populates="players")


class UserTG(DBBase):
    __tablename__ = 'user_tg'

    chat_id: sa_orm.Mapped[int] = sa_orm.mapped_column(unique=True, nullable=True)
    username: sa_orm.Mapped[str]
