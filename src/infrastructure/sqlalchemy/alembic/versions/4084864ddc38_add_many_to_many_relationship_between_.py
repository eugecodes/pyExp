"""Add many to many relationship between commissions and rates

Revision ID: 4084864ddc38
Revises: 921571f8c22c
Create Date: 2023-07-27 10:31:19.529853

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4084864ddc38'
down_revision = '921571f8c22c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('commissions_rates',
    sa.Column('commission_id', sa.Integer(), nullable=True),
    sa.Column('rate_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['commission_id'], ['commission.id'], ),
    sa.ForeignKeyConstraint(['rate_id'], ['rate.id'], ),
    sa.UniqueConstraint('commission_id', 'rate_id')
    )
    op.drop_constraint('rate_commission_id_fkey', 'rate', type_='foreignkey')
    op.drop_column('rate', 'commission_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rate', sa.Column('commission_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('rate_commission_id_fkey', 'rate', 'commission', ['commission_id'], ['id'])
    op.drop_table('commissions_rates')
    # ### end Alembic commands ###
