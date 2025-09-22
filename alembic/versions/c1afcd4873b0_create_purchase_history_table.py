"""create purchase_history table

Revision ID: c1afcd4873b0
Revises: 06042afef775
Create Date: 2025-09-22 00:04:54.609817

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1afcd4873b0'
down_revision = '06042afef775'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("visible", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_purchase_history_user_created_at",
        "purchase_history",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_purchase_history_text_fts",
        "purchase_history",
        [sa.text("to_tsvector('russian', text)")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_purchase_history_payload",
        "purchase_history",
        ["payload"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_purchase_history_payload", table_name="purchase_history")
    op.drop_index("ix_purchase_history_text_fts", table_name="purchase_history")
    op.drop_index("ix_purchase_history_user_created_at", table_name="purchase_history")
    op.drop_table("purchase_history")