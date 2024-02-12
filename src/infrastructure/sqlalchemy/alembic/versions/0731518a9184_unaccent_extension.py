"""unaccent extension

Revision ID: 0731518a9184
Revises: b90b23adf6c9
Create Date: 2023-01-24 13:57:50.117144

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0731518a9184'
down_revision = 'bc51efa2abf6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(sa.text("DROP EXTENSION IF EXISTS unaccent;"))
    # ### end Alembic commands ###