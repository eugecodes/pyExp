"""model_standarization

Revision ID: f1e31b863deb
Revises: 725b1ee6c74d
Create Date: 2023-03-01 11:51:52.061672

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1e31b863deb'
down_revision = '725b1ee6c74d'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('energy_costs', 'energy_cost')
    op.rename_table('users', 'user')
    op.rename_table('rate_types', 'rate_type')
    op.rename_table('tokens', 'token')


def downgrade():
    op.rename_table('energy_cost', 'energy_costs')
    op.rename_table('user', 'users')
    op.rename_table('rate_type', 'rate_types')
    op.rename_table('token', 'tokens')
