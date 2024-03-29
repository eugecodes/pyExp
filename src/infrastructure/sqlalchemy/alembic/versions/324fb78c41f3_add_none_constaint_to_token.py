"""Add None constaint to token

Revision ID: 324fb78c41f3
Revises: a9becfb7e748
Create Date: 2023-01-11 12:44:05.249565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '324fb78c41f3'
down_revision = 'a9becfb7e748'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'tokens', ['token'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'tokens', type_='unique')
    # ### end Alembic commands ###
