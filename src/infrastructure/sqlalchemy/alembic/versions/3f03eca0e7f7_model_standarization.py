"""model_standarization

Revision ID: 3f03eca0e7f7
Revises: f1e31b863deb
Create Date: 2023-03-01 12:12:54.156107

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3f03eca0e7f7'
down_revision = 'f1e31b863deb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('energy_cost', sa.Column('is_protected', sa.Boolean(), nullable=False, server_default=sa.text('False')))
    op.execute("UPDATE energy_cost SET create_at = now() WHERE create_at IS NULL")
    op.alter_column('energy_cost', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               server_default=sa.text('now()'))
    op.execute("UPDATE energy_cost SET is_deleted = false WHERE is_deleted IS NULL")
    op.alter_column('energy_cost', 'is_deleted',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               server_default=sa.text('False'))
    op.drop_index('ix_energy_costs_concept', table_name='energy_cost')
    op.drop_index('ix_energy_costs_id', table_name='energy_cost')
    op.create_index(op.f('ix_energy_cost_concept'), 'energy_cost', ['concept'], unique=False)
    op.execute("UPDATE rate_type SET create_at = now() WHERE create_at IS NULL")
    op.alter_column('rate_type', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               server_default=sa.text('now()'))
    op.drop_index('ix_rate_types_energy_type', table_name='rate_type')
    op.drop_index('ix_rate_types_id', table_name='rate_type')
    op.create_index(op.f('ix_rate_type_energy_type'), 'rate_type', ['energy_type'], unique=False)
    op.drop_index('ix_tokens_id', table_name='token')
    op.execute("UPDATE \"user\" SET create_at = now() WHERE create_at IS NULL")
    op.alter_column('user', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               server_default=sa.text('now()'))
    op.drop_index('ix_users_email', table_name='user')
    op.drop_index('ix_users_first_name', table_name='user')
    op.drop_index('ix_users_id', table_name='user')
    op.drop_index('ix_users_last_name', table_name='user')
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_first_name'), 'user', ['first_name'], unique=False)
    op.create_index(op.f('ix_user_last_name'), 'user', ['last_name'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_last_name'), table_name='user')
    op.drop_index(op.f('ix_user_first_name'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.create_index('ix_users_last_name', 'user', ['last_name'], unique=False)
    op.create_index('ix_users_id', 'user', ['id'], unique=False)
    op.create_index('ix_users_first_name', 'user', ['first_name'], unique=False)
    op.create_index('ix_users_email', 'user', ['email'], unique=False)
    op.alter_column('user', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.create_index('ix_tokens_id', 'token', ['id'], unique=False)
    op.drop_index(op.f('ix_rate_type_energy_type'), table_name='rate_type')
    op.create_index('ix_rate_types_id', 'rate_type', ['id'], unique=False)
    op.create_index('ix_rate_types_energy_type', 'rate_type', ['energy_type'], unique=False)
    op.alter_column('rate_type', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_index(op.f('ix_energy_cost_concept'), table_name='energy_cost')
    op.create_index('ix_energy_costs_id', 'energy_cost', ['id'], unique=False)
    op.create_index('ix_energy_costs_concept', 'energy_cost', ['concept'], unique=False)
    op.alter_column('energy_cost', 'is_deleted',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('energy_cost', 'create_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_column('energy_cost', 'is_protected')
    # ### end Alembic commands ###