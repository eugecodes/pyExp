"""nullable user_id

Revision ID: 63b97ff85506
Revises: dd0cb128d52d
Create Date: 2023-02-07 07:48:17.563942

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Integer, Numeric, String, Boolean
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '63b97ff85506'
down_revision = 'dd0cb128d52d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('energy_costs', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    data_upgrades()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    data_downgrades()
    op.alter_column('energy_costs', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def data_upgrades():
    # Add any optional data upgrade migrations here!

    energy_costs = table('energy_costs',
        column('concept', String),
        column('amount', Numeric(14,6)),
        column('user_id', Integer),
        column('is_active', Boolean),
    )

    op.bulk_insert(energy_costs,
        [
            {'concept': 'Iva', 'amount': 21, 'user_id': None, 'is_active': True},
            {'concept': 'Iva Redcido', 'amount': 5, 'user_id': None, 'is_active': True},
            {'concept': 'Impuestos de hidrocarburos', 'amount': 0.00234, 'user_id': None, 'is_active': True},
            {'concept': 'Impuestos eléctricos', 'amount': 5.1127, 'user_id': None, 'is_active': True},
        ]
    )

def data_downgrades():
    # Add any optional data downgrade migrations here!

    op.execute("delete from energy_costs")
    