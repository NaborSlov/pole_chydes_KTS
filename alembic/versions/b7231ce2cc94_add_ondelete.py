"""add_ondelete

Revision ID: b7231ce2cc94
Revises: 8bb33514e946
Create Date: 2023-03-15 22:48:16.899424

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7231ce2cc94'
down_revision = '8bb33514e946'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('round_player_id_fkey', 'round', type_='foreignkey')
    op.create_foreign_key(None, 'round', 'player', ['player_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'round', type_='foreignkey')
    op.create_foreign_key('round_player_id_fkey', 'round', 'player', ['player_id'], ['id'])
    # ### end Alembic commands ###