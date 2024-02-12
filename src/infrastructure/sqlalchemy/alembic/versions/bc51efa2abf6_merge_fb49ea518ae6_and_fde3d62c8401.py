"""merge fb49ea518ae6 and fde3d62c8401

Revision ID: bc51efa2abf6
Revises: fb49ea518ae6, fde3d62c8401
Create Date: 2023-01-26 09:00:12.322722

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc51efa2abf6'
down_revision = ('fb49ea518ae6', 'fde3d62c8401')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
