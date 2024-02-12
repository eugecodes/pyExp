"""rename_user_table

Revision ID: bcd7c4048d8a
Revises: 3f03eca0e7f7
Create Date: 2023-03-01 13:19:09.762352

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bcd7c4048d8a'
down_revision = '3f03eca0e7f7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_user_email', table_name='user')
    op.drop_index('ix_user_first_name', table_name='user')
    op.drop_index('ix_user_last_name', table_name='user')
    
    op.rename_table('user', 'user_table')
    
    op.create_index(op.f('ix_user_table_email'), 'user_table', ['email'], unique=True)
    op.create_index(op.f('ix_user_table_first_name'), 'user_table', ['first_name'], unique=False)
    op.create_index(op.f('ix_user_table_last_name'), 'user_table', ['last_name'], unique=False)

    op.drop_constraint('energy_costs_user_id_fkey', 'energy_cost', type_='foreignkey')
    op.create_foreign_key(None, 'energy_cost', 'user_table', ['user_id'], ['id'])
    op.drop_constraint('rate_types_user_id_fkey', 'rate_type', type_='foreignkey')
    op.create_foreign_key(None, 'rate_type', 'user_table', ['user_id'], ['id'])
    op.drop_constraint('tokens_user_id_fkey', 'token', type_='foreignkey')
    op.create_foreign_key(None, 'token', 'user_table', ['user_id'], ['id'])


def downgrade():

    op.drop_index(op.f('ix_user_table_last_name'), table_name='user_table')
    op.drop_index(op.f('ix_user_table_first_name'), table_name='user_table')
    op.drop_index(op.f('ix_user_table_email'), table_name='user_table')
    
    op.rename_table('user_table', 'user')

    op.create_index('ix_user_last_name', 'user', ['last_name'], unique=False)
    op.create_index('ix_user_first_name', 'user', ['first_name'], unique=False)
    op.create_index('ix_user_email', 'user', ['email'], unique=False)
    
    op.drop_constraint(None, 'token', type_='foreignkey')
    op.create_foreign_key('tokens_user_id_fkey', 'token', 'user', ['user_id'], ['id'])
    op.drop_constraint(None, 'rate_type', type_='foreignkey')
    op.create_foreign_key('rate_types_user_id_fkey', 'rate_type', 'user', ['user_id'], ['id'])
    op.drop_constraint(None, 'energy_cost', type_='foreignkey')
    op.create_foreign_key('energy_costs_user_id_fkey', 'energy_cost', 'user', ['user_id'], ['id'])
