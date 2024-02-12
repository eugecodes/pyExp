"""Add commissions to suggested rate

Revision ID: 921571f8c22c
Revises: 7ff7c00b9e73
Create Date: 2023-07-25 10:20:51.059616

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '921571f8c22c'
down_revision = '7ff7c00b9e73'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('suggested_rate', sa.Column('total_commission', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('suggested_rate', sa.Column('other_costs_commission', sa.Numeric(precision=10, scale=2), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('suggested_rate', 'other_costs_commission')
    op.drop_column('suggested_rate', 'total_commission')
    # ### end Alembic commands ###