"""rate type name unique

Revision ID: d9a5f2b04af5
Revises: c25b66436044
Create Date: 2023-05-08 17:28:05.261542

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd9a5f2b04af5'
down_revision = 'c25b66436044'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'rate_type', ['name', 'energy_type'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'rate_type', type_='unique')
    # ### end Alembic commands ###