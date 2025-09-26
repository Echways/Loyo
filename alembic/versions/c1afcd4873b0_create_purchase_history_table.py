"""create purchase_history table

Revision ID: c1afcd4873b0
Revises: 06042afef775
Create Date: 2025-09-22 00:04:54.609817

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c1afcd4873b0"
down_revision = "06042afef775"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_history",
        sa.Column(
            "purchase_id", sa.String(length=64), primary_key=True, nullable=False
        ),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("product_id", sa.String(length=128), nullable=True),
        sa.Column("product_title", sa.Text, nullable=True),
        sa.Column("price", sa.Integer, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("confirmed_at", sa.DateTime, nullable=True),
        sa.Column("confirmed_by", sa.BigInteger, nullable=True),
        sa.Column("awarded_points", sa.Integer, nullable=True),
    )

    # Индексы (purchase_id указан как индекс=True в модели — делаю явный индекс,
    # хотя PK обычно уже индексируется; если не нужно — можно убрать)
    op.create_index(
        "ix_purchase_history_purchase_id",
        "purchase_history",
        ["purchase_id"],
    )
    op.create_index(
        "ix_purchase_history_user_id",
        "purchase_history",
        ["user_id"],
    )
    op.create_index(
        "ix_purchase_history_product_id",
        "purchase_history",
        ["product_id"],
    )
    # индекс по payload (GIN) — опционально, если часто делаете JSONB-операции/фильтрацию
    op.create_index(
        "ix_purchase_history_payload",
        "purchase_history",
        ["payload"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_purchase_history_payload", table_name="purchase_history")
    op.drop_index("ix_purchase_history_product_id", table_name="purchase_history")
    op.drop_index("ix_purchase_history_user_id", table_name="purchase_history")
    op.drop_index("ix_purchase_history_purchase_id", table_name="purchase_history")
    op.drop_table("purchase_history")
