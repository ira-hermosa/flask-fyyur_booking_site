"""empty message

Revision ID: 5225b225170f
Revises: 8cf31d27bb26
Create Date: 2020-07-11 20:20:53.417606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5225b225170f'
down_revision = '8cf31d27bb26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Venue', 'website',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Venue', 'website',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
    # ### end Alembic commands ###
