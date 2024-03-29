"""Create contract model

Revision ID: 80986a0ee8a2
Revises: 2b0408b1d6bc
Create Date: 2023-10-27 09:59:22.314476

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "80986a0ee8a2"
down_revision = "2b0408b1d6bc"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "contract",
        sa.Column(
            "status",
            sa.Enum(
                "INCOMPLETE",
                "REQUESTED",
                "WAITING_MARKETER",
                "WAITING_CLIENT_SIGN",
                "SIGNED",
                "ACTIVATED",
                "FINISHED",
                "MARKETER_ISSUE",
                "DISTRIBUTOR_ISSUE",
                "CANCELLED",
                name="contractstatusenum",
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("create_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("supply_point_id", sa.Integer(), nullable=False),
        sa.Column("rate_id", sa.Integer(), nullable=False),
        sa.Column("saving_study_id", sa.Integer(), nullable=True),
        sa.Column("power_1", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("power_2", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("power_3", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("power_4", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("power_5", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("power_6", sa.Numeric(precision=14, scale=6), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("expected_end_date", sa.DateTime(), nullable=True),
        sa.Column("preferred_start_date", sa.DateTime(), nullable=True),
        sa.Column("period", sa.Integer(), nullable=True),
        sa.Column("signature_first_name", sa.String(length=128), nullable=False),
        sa.Column("signature_last_name", sa.String(length=128), nullable=False),
        sa.Column("signature_dni", sa.String(length=20), nullable=True),
        sa.Column("signature_email", sa.String(length=256), nullable=True),
        sa.Column("signature_phone", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(
            ["rate_id"],
            ["rate.id"],
        ),
        sa.ForeignKeyConstraint(
            ["saving_study_id"],
            ["saving_study.id"],
        ),
        sa.ForeignKeyConstraint(
            ["supply_point_id"],
            ["supply_point.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_table.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("contract")
    # ### end Alembic commands ###
