"""create pending table

Revision ID: d5deddc91155
Revises: c1afcd4873b0
Create Date: 2025-09-24 13:48:43.306008

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5deddc91155'
down_revision = 'c1afcd4873b0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pending",
        sa.Column("purchase_id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=True),
        sa.Column("product_title", sa.Text(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_by", sa.BigInteger(), nullable=True),
        sa.Column("awarded_points", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index("ix_pending_user_id", "pending", ["user_id"])


def downgrade():
    op.drop_index("ix_pending_user_id", table_name="pending")
    op.drop_table("pending")
