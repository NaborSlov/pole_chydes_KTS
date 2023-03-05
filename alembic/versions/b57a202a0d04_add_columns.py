"""add columns

Revision ID: b57a202a0d04
Revises: 29b20e788c2c
Create Date: 2023-03-05 16:38:31.834465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b57a202a0d04'
down_revision = '29b20e788c2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admins',
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('password', sa.VARCHAR(length=255), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.add_column('game', sa.Column('round_id', sa.Integer(), nullable=True))
    op.add_column('game', sa.Column('question_id', sa.Integer(), nullable=True))
    op.add_column('game', sa.Column('answered', sa.String(), nullable=False))
    op.add_column('game', sa.Column('started', sa.Boolean(), nullable=False))
    op.create_foreign_key(None, 'game', 'round', ['round_id'], ['id'])
    op.create_foreign_key(None, 'game', 'question', ['question_id'], ['id'])
    op.add_column('player', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('game_id', sa.Integer(), nullable=True))
    op.add_column('player', sa.Column('score', sa.Integer(), nullable=False))
    op.add_column('player', sa.Column('fails', sa.Boolean(), nullable=False))
    op.create_foreign_key(None, 'player', 'user_tg', ['user_id'], ['id'])
    op.create_foreign_key(None, 'player', 'game', ['game_id'], ['id'])
    op.add_column('question', sa.Column('description', sa.String(), nullable=False))
    op.add_column('question', sa.Column('answer', sa.String(), nullable=False))
    op.add_column('round', sa.Column('player_id', sa.Integer(), nullable=True))
    op.add_column('round', sa.Column('finished', sa.DateTime(), nullable=True))
    op.create_foreign_key(None, 'round', 'player', ['player_id'], ['id'])
    op.add_column('user_tg', sa.Column('chat_id', sa.Integer(), nullable=True))
    op.add_column('user_tg', sa.Column('username', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'user_tg', ['chat_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user_tg', type_='unique')
    op.drop_column('user_tg', 'username')
    op.drop_column('user_tg', 'chat_id')
    op.drop_constraint(None, 'round', type_='foreignkey')
    op.drop_column('round', 'finished')
    op.drop_column('round', 'player_id')
    op.drop_column('question', 'answer')
    op.drop_column('question', 'description')
    op.drop_constraint(None, 'player', type_='foreignkey')
    op.drop_constraint(None, 'player', type_='foreignkey')
    op.drop_column('player', 'fails')
    op.drop_column('player', 'score')
    op.drop_column('player', 'game_id')
    op.drop_column('player', 'user_id')
    op.drop_constraint(None, 'game', type_='foreignkey')
    op.drop_constraint(None, 'game', type_='foreignkey')
    op.drop_column('game', 'started')
    op.drop_column('game', 'answered')
    op.drop_column('game', 'question_id')
    op.drop_column('game', 'round_id')
    op.drop_table('admins')
    # ### end Alembic commands ###