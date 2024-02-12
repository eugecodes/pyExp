"""Update SavingStudy table with new mandatory fields

Revision ID: 8b82de544afd
Revises: 403d4e6ce873
Create Date: 2023-07-03 08:24:27.293664

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8b82de544afd'
down_revision = '403d4e6ce873'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    energy_type = postgresql.ENUM('electricity', 'inactive', 'gas', name='energytype')
    energy_type.create(op.get_bind(), checkfirst=True)

    op.add_column('saving_study', sa.Column('energy_type', energy_type, nullable=True))
    op.execute("UPDATE saving_study SET energy_type = 'electricity'")
    op.alter_column('saving_study', 'energy_type', nullable=False)

    op.add_column('saving_study', sa.Column('is_existing_client', sa.Boolean(), nullable=True))
    op.execute("UPDATE saving_study SET is_existing_client = False")
    op.alter_column('saving_study', 'is_existing_client', nullable=False)

    op.add_column('saving_study', sa.Column('is_from_sips', sa.Boolean(), nullable=True))
    op.execute("UPDATE saving_study SET is_from_sips = False")
    op.alter_column('saving_study', 'is_from_sips', nullable=False)

    op.add_column('saving_study', sa.Column('is_compare_conditions', sa.Boolean(), nullable=True))
    op.execute("UPDATE saving_study SET is_compare_conditions = False")
    op.alter_column('saving_study', 'is_compare_conditions', nullable=False)

    op.alter_column('saving_study', 'power_price_1',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_2',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_3',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_4',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_5',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_6',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_1',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=False)
    op.alter_column('saving_study', 'energy_price_2',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_3',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_4',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_5',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_6',
               existing_type=sa.NUMERIC(precision=10, scale=2),
               type_=sa.Numeric(precision=10, scale=6),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'energy_price_6',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_5',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_4',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_3',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_2',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'energy_price_1',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=False)
    op.alter_column('saving_study', 'power_price_6',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_5',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_4',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_3',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_2',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.alter_column('saving_study', 'power_price_1',
               existing_type=sa.Numeric(precision=10, scale=6),
               type_=sa.NUMERIC(precision=10, scale=2),
               existing_nullable=True)
    op.drop_column('saving_study', 'is_compare_conditions')
    op.drop_column('saving_study', 'is_from_sips')
    op.drop_column('saving_study', 'is_existing_client')
    op.drop_column('saving_study', 'energy_type')

    # drop enum
    op.execute("DROP TYPE energytype")
    # ### end Alembic commands ###
