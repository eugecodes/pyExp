"""energy_type removed

Revision ID: c25b66436044
Revises: 6d205345717a
Create Date: 2023-05-08 10:00:49.615262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c25b66436044'
down_revision = '6d205345717a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rate', 'energy_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rate', sa.Column('energy_type', sa.VARCHAR(length=11), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
