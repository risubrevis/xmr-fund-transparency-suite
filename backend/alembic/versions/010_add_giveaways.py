"""add giveaways table and transactions.giveaway_id

Revision ID: 010
Revises: 009
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "giveaways",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("public_uuid", sa.String(length=36), nullable=True),
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=4096), nullable=True),
        sa.Column("deposit_address", sa.String(length=95), nullable=False),
        sa.Column("min_amount_xmr", sa.Numeric(precision=20, scale=12), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("instructions_after_end", sa.String(length=4096), nullable=True),
        sa.Column("widget_background_color", sa.String(length=7), nullable=True),
        sa.Column("widget_text_color", sa.String(length=7), nullable=True),
        sa.Column("public_website", sa.String(length=255), nullable=True),
        sa.Column("winning_transaction_id", sa.UUID(), nullable=True),
        sa.Column("winning_block_hash", sa.String(length=64), nullable=True),
        sa.Column("winning_block_height", sa.Integer(), nullable=True),
        sa.Column(
            "is_closed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "deposit_address", name=op.f("uq_giveaways_deposit_address")
        ),
    )
    op.create_index(
        op.f("ix_giveaways_public_uuid"), "giveaways", ["public_uuid"], unique=True
    )

    # Allow transactions to be linked to either a fund or a giveaway.
    # fund_id is already nullable in the schema; add giveaway_id as nullable.
    op.add_column(
        "transactions",
        sa.Column("giveaway_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_giveaway_id",
        "transactions",
        "giveaways",
        ["giveaway_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_transactions_giveaway_id"), "transactions", ["giveaway_id"]
    )
    op.create_check_constraint(
        "tx_fund_xor_giveaway",
        "transactions",
        "(fund_id IS NOT NULL AND giveaway_id IS NULL) "
        "OR (fund_id IS NULL AND giveaway_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("tx_fund_xor_giveaway", "transactions", type_="check")
    op.drop_index(op.f("ix_transactions_giveaway_id"), table_name="transactions")
    op.drop_constraint(
        "fk_transactions_giveaway_id", "transactions", type_="foreignkey"
    )
    op.drop_column("transactions", "giveaway_id")
    op.drop_index(op.f("ix_giveaways_public_uuid"), table_name="giveaways")
    op.drop_table("giveaways")
