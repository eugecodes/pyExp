"""current_rate_type_id in SavingStudy table is now nullable

Revision ID: 18cb77af25e0
Revises: 8b82de544afd
Create Date: 2023-07-03 09:36:53.340372

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18cb77af25e0'
down_revision = '8b82de544afd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'current_rate_type_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('saving_study', 'current_rate_type_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###