"""Create Supply Point

Revision ID: 2b0408b1d6bc
Revises: 1ea3d826ae18
Create Date: 2023-10-19 12:09:25.877560

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2b0408b1d6bc"
down_revision = "1ea3d826ae18"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "supply_point",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("create_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column(
            "energy_type",
            sa.Enum("electricity", "gas", name="energytypesupply"),
            nullable=False,
        ),
        sa.Column("cups", sa.String(length=124), nullable=False),
        sa.Column("alias", sa.String(length=64), nullable=True),
        sa.Column("supply_address", sa.String(length=256), nullable=True),
        sa.Column("supply_postal_code", sa.String(length=10), nullable=True),
        sa.Column("supply_city", sa.String(length=256), nullable=True),
        sa.Column("supply_province", sa.String(length=256), nullable=True),
        sa.Column("bank_account_holder", sa.String(length=64), nullable=True),
        sa.Column("bank_account_number", sa.String(length=64), nullable=True),
        sa.Column("fiscal_address", sa.String(length=256), nullable=True),
        sa.Column("is_renewable", sa.Boolean(), nullable=False),
        sa.Column("max_available_power", sa.Integer(), nullable=True),
        sa.Column("voltage", sa.Integer(), nullable=True),
        sa.Column(
            "counter_type",
            sa.Enum("normal", "telematic", name="countertype"),
            nullable=True,
        ),
        sa.Column(
            "counter_property",
            sa.Enum("self", "marketer", "other", name="ownertype"),
            nullable=True,
        ),
        sa.Column("counter_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["client.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_table.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cups"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("supply_point")
    # ### end Alembic commands ###
