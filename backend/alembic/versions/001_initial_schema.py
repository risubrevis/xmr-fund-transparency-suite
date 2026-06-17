"""Initial schema - funds and transactions tables.

Revision ID: 001
Revises:
Create Date: 2026-06-17

"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "funds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("public_uuid", sa.String(length=36), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("primary_address", sa.String(length=95), nullable=False),
        sa.Column("view_key", sa.String(length=512), nullable=False),
        sa.Column("start_height", sa.Integer(), nullable=False),
        sa.Column("last_scanned_height", sa.Integer(), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_error", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funds_public_uuid"), "funds", ["public_uuid"], unique=True)

    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fund_id", sa.UUID(), nullable=True),
        sa.Column("txid", sa.String(length=64), nullable=False),
        sa.Column("amount_atomic", sa.BigInteger(), nullable=False),
        sa.Column("amount_xmr", sa.Numeric(precision=20, scale=12), nullable=False),
        sa.Column("confirmations", sa.Integer(), server_default=sa.text("0")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlock_time", sa.BigInteger(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transactions_txid"), "transactions", ["txid"], unique=False
    )
    op.create_index(
        op.f("ix_transactions_height"), "transactions", ["height"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_height"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_txid"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_funds_public_uuid"), table_name="funds")
    op.drop_table("funds")
