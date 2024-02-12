"""user type field

Revision ID: 06cc23fd1db2
Revises: 4cc52ed7e7f1
Create Date: 2023-06-06 15:08:55.114041

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06cc23fd1db2'
down_revision = '4cc52ed7e7f1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_table', sa.Column('type', sa.String(length=32), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_table', 'type')
    # ### end Alembic commands ###
