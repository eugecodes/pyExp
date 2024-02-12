"""Create Contact model

Revision ID: a7e6d78834f2
Revises: 2204e8f0bbd6
Create Date: 2023-10-17 08:25:41.322999

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7e6d78834f2"
down_revision = "2204e8f0bbd6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("contact", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(None, "contact", "user_table", ["user_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "contact", type_="foreignkey")
    op.drop_column("contact", "user_id")
    # ### end Alembic commands ###
