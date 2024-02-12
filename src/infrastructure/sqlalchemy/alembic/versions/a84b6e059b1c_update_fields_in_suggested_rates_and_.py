"""Update fields in suggested rates and studies

Revision ID: a84b6e059b1c
Revises: 6d5d0abafaf7
Create Date: 2023-07-06 06:34:54.641531

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a84b6e059b1c'
down_revision = '6d5d0abafaf7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'annual_consumption',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=False)
    op.add_column('suggested_rate', sa.Column('is_full_renewable', sa.Boolean(), nullable=False))
    op.add_column('suggested_rate', sa.Column('has_net_metering', sa.Boolean(), nullable=False))
    op.add_column('suggested_rate', sa.Column('net_metering_value', sa.Numeric(precision=10, scale=2), nullable=False))
    op.add_column('suggested_rate', sa.Column('profit_margin_type', sa.String(length=13), nullable=False))
    op.add_column('suggested_rate', sa.Column('min_profit_margin', sa.Numeric(precision=14, scale=6), nullable=False))
    op.add_column('suggested_rate', sa.Column('max_profit_margin', sa.Numeric(precision=14, scale=6), nullable=False))
    op.drop_column('suggested_rate', 'surplus_price')
    op.drop_column('suggested_rate', 'net_metering')
    op.drop_column('suggested_rate', 'renewable')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('suggested_rate', sa.Column('renewable', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('suggested_rate', sa.Column('net_metering', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('suggested_rate', sa.Column('surplus_price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False))
    op.drop_column('suggested_rate', 'max_profit_margin')
    op.drop_column('suggested_rate', 'min_profit_margin')
    op.drop_column('suggested_rate', 'profit_margin_type')
    op.drop_column('suggested_rate', 'net_metering_value')
    op.drop_column('suggested_rate', 'has_net_metering')
    op.drop_column('suggested_rate', 'is_full_renewable')
    op.alter_column('saving_study', 'annual_consumption',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               nullable=True)
    # ### end Alembic commands ###