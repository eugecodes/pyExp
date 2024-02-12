"""energy_type as Enum

Revision ID: b8a667b89f23
Revises: 90d920143e2a
Create Date: 2023-03-06 15:22:25.604243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8a667b89f23'
down_revision = '90d920143e2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('rate_type', 'energy_type',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.String(length=11),
               existing_nullable=False)
    op.drop_index('ix_rate_type_energy_type', table_name='rate_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_rate_type_energy_type', 'rate_type', ['energy_type'], unique=False)
    op.alter_column('rate_type', 'energy_type',
               existing_type=sa.String(length=11),
               type_=sa.VARCHAR(length=16),
               existing_nullable=False)
    # ### end Alembic commands ###
