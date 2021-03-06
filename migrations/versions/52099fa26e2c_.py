"""empty message

Revision ID: 52099fa26e2c
Revises: b9aff602478a
Create Date: 2022-06-26 21:59:06.102156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52099fa26e2c'
down_revision = 'b9aff602478a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('voter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('election_id', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=58), nullable=False),
    sa.Column('matric_no', sa.String(length=40), nullable=False),
    sa.ForeignKeyConstraint(['election_id'], ['elections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('voter')
    # ### end Alembic commands ###
