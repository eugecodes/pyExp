"""Add status message to contract

Revision ID: 7c0b14c92043
Revises: 80986a0ee8a2
Create Date: 2023-11-08 12:20:18.470951

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7c0b14c92043"
down_revision = "80986a0ee8a2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "contract", sa.Column("status_message", sa.String(length=256), nullable=True)
    )


def downgrade():
    op.drop_column("contract", "status_message")
