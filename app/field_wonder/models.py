from app.store.database import db
import sqlalchemy.orm as sa_orm
import sqlalchemy as sa


class SessionGame(db):
    __tablename__ = 'session_game'

    id: sa_orm.Mapped[int] = sa_orm.mapped_column(primary_key=True)
    question: sa_orm.Mapped[str] = sa_orm.mapped_column()
    answer: sa_orm.Mapped[str] = sa_orm.mapped_column()
    answered: sa_orm.Mapped[str] = sa_orm.mapped_column()
    players: sa_orm.Mapped[list['Player']] = sa_orm.relationship(back_populates='session_game')


class Player(db):
    __tablename__ = 'player'

    id: sa_orm.Mapped[int] = sa_orm.mapped_column(primary_key=True)
    scores: sa_orm.Mapped[int] = sa_orm.mapped_column()
    session_game_id: sa_orm.Mapped[int] = sa_orm.mapped_column(sa.ForeignKey('session_game.id'))
    session_game: sa_orm.Mapped['SessionGame'] = sa_orm.relationship(back_populates='players')
