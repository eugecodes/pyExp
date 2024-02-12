"""Make some fields nullable

Revision ID: 6d5d0abafaf7
Revises: 18cb77af25e0
Create Date: 2023-07-04 10:39:59.477465

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6d5d0abafaf7'
down_revision = '18cb77af25e0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'analyzed_days',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('saving_study', 'client_type',
               existing_type=postgresql.ENUM('company', 'self_employed', 'particular', 'community_owners', name='clienttype'),
               nullable=True)
    op.alter_column('saving_study', 'energy_price_1',
               existing_type=sa.NUMERIC(precision=10, scale=6),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'energy_price_1',
               existing_type=sa.NUMERIC(precision=10, scale=6),
               nullable=False)
    op.alter_column('saving_study', 'client_type',
               existing_type=postgresql.ENUM('company', 'self_employed', 'particular', 'community_owners', name='clienttype'),
               nullable=False)
    op.alter_column('saving_study', 'analyzed_days',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
