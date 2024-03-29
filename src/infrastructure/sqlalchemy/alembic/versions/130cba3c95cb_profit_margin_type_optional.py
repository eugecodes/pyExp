"""profit margin type optional

Revision ID: 130cba3c95cb
Revises: a84b6e059b1c
Create Date: 2023-07-06 09:43:55.071852

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '130cba3c95cb'
down_revision = 'a84b6e059b1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('suggested_rate', 'profit_margin_type',
               existing_type=sa.VARCHAR(length=13),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('suggested_rate', 'profit_margin_type',
               existing_type=sa.VARCHAR(length=13),
               nullable=False)
    # ### end Alembic commands ###
