"""init migration

Revision ID: 29b20e788c2c
Revises: 
Create Date: 2023-02-28 13:51:17.670869

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '29b20e788c2c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('question',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('game',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('player',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('round',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('user_tg',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('round')
    op.drop_table('question')
    op.drop_table('player')
    op.drop_table('game')
    # ### end Alembic commands ###
