"""is_deleted field added

Revision ID: 531e45a00101
Revises: 0731518a9184
Create Date: 2023-02-01 13:57:43.113765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '531e45a00101'
down_revision = '0731518a9184'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rate_types', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('False')))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rate_types', 'is_deleted')
    # ### end Alembic commands ###