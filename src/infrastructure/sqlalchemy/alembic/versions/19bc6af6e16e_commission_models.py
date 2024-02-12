"""commission models

Revision ID: 19bc6af6e16e
Revises: 4be789b5f1cc
Create Date: 2023-05-29 15:55:24.816861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19bc6af6e16e'
down_revision = '4be789b5f1cc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('commission',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=124), nullable=False),
    sa.Column('range_type', sa.String(length=11), nullable=True),
    sa.Column('min_consumption', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('max_consumption', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('min_power', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('max_power', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('percentage_Test_commission', sa.Integer(), nullable=True),
    sa.Column('rate_type_segmentation', sa.Boolean(), nullable=True),
    sa.Column('Test_commission', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.Column('rate_type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['rate_type_id'], ['rate_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('rate', sa.Column('commission_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'rate', 'commission', ['commission_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'rate', type_='foreignkey')
    op.drop_column('rate', 'commission_id')
    op.drop_table('commission')
    # ### end Alembic commands ###