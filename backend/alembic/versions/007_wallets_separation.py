"""Introduce wallets table and separate wallet concerns from funds.

- Create new wallets table with wallet-related fields (primary_address,
  view_key, start_height, scan metadata).
- Add wallet_id FK to funds, transactions, and posts.
- Migrate existing data: move wallet fields from funds into a new wallets row,
  populate wallet_id in all tables, set deposit_address to NOT NULL with UNIQUE.
- Drop wallet-related columns from funds.

Revision ID: 007
Revises: 006
Create Date: 2026-07-02

"""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"


def upgrade() -> None:
    # 1. Create wallets table
    op.create_table(
        "wallets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("uuid", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("primary_address", sa.String(95), nullable=False),
        sa.Column("view_key", sa.String(512), nullable=False),
        sa.Column("start_height", sa.Integer(), nullable=False),
        sa.Column("last_scanned_height", sa.Integer(), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_error", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallets_uuid", "wallets", ["uuid"], unique=True)

    # 2. Migrate data: create a wallet row from the existing single fund
    #    Generate a proper UUID for each wallet using gen_random_uuid()
    op.execute(
        """
        INSERT INTO wallets (id, uuid, name, primary_address, view_key, start_height,
                             last_scanned_height, last_scan_at, scan_error, created_at,
                             updated_at, is_active)
        SELECT id,
               gen_random_uuid()::text,
               label || ' Wallet',
               primary_address,
               view_key,
               start_height,
               last_scanned_height,
               last_scan_at,
               scan_error,
               created_at,
               updated_at,
               is_active
        FROM funds
        """
    )

    # 3. Add wallet_id column to funds (nullable first for migration)
    op.add_column("funds", sa.Column("wallet_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_funds_wallet_id",
        "funds",
        "wallets",
        ["wallet_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_funds_wallet_id", "funds", ["wallet_id"])

    # 4. Populate wallet_id in funds from the migrated wallet row
    op.execute("UPDATE funds SET wallet_id = id")

    # 5. Add wallet_id column to transactions (nullable first)
    op.add_column("transactions", sa.Column("wallet_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_transactions_wallet_id",
        "transactions",
        "wallets",
        ["wallet_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_transactions_wallet_id", "transactions", ["wallet_id"])

    # 6. Populate wallet_id in transactions from fund -> wallet relationship
    op.execute(
        """
        UPDATE transactions t
        SET wallet_id = f.wallet_id
        FROM funds f
        WHERE t.fund_id = f.id
        """
    )

    # 7. Add wallet_id column to posts (nullable first)
    op.add_column("posts", sa.Column("wallet_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_posts_wallet_id",
        "posts",
        "wallets",
        ["wallet_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_posts_wallet_id", "posts", ["wallet_id"])

    # 8. Populate wallet_id in posts from fund -> wallet relationship
    op.execute(
        """
        UPDATE posts p
        SET wallet_id = f.wallet_id
        FROM funds f
        WHERE p.fund_id = f.id
        """
    )

    # 9. Make deposit_address NOT NULL and set unique
    #    First populate NULLs with primary_address (shouldn't happen but be safe)
    op.execute(
        "UPDATE funds SET deposit_address = primary_address WHERE deposit_address IS NULL"
    )
    op.alter_column("funds", "deposit_address", nullable=False)
    op.create_index(
        "ix_funds_deposit_address", "funds", ["deposit_address"], unique=True
    )

    # 10. Now make wallet_id NOT NULL (data has been populated)
    op.alter_column("funds", "wallet_id", nullable=False)
    op.alter_column("transactions", "wallet_id", nullable=False)
    op.alter_column("posts", "wallet_id", nullable=False)

    # 11. Drop wallet-related columns from funds
    op.drop_column("funds", "primary_address")
    op.drop_column("funds", "view_key")
    op.drop_column("funds", "start_height")
    op.drop_column("funds", "last_scanned_height")
    op.drop_column("funds", "last_scan_at")
    op.drop_column("funds", "scan_error")


def downgrade() -> None:
    # 1. Re-add wallet-related columns to funds (nullable first)
    op.add_column("funds", sa.Column("scan_error", sa.String(500), nullable=True))
    op.add_column(
        "funds", sa.Column("last_scan_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "funds",
        sa.Column("last_scanned_height", sa.Integer(), nullable=True),
    )
    op.add_column("funds", sa.Column("start_height", sa.Integer(), nullable=True))
    op.add_column("funds", sa.Column("view_key", sa.String(512), nullable=True))
    op.add_column("funds", sa.Column("primary_address", sa.String(95), nullable=True))

    # 2. Migrate data back from wallets to funds
    op.execute(
        """
        UPDATE funds f
        SET primary_address = w.primary_address,
            view_key = w.view_key,
            start_height = w.start_height,
            last_scanned_height = w.last_scanned_height,
            last_scan_at = w.last_scan_at,
            scan_error = w.scan_error
        FROM wallets w
        WHERE f.wallet_id = w.id
        """
    )

    # 3. Make re-added columns NOT NULL (data has been populated)
    op.alter_column("funds", "primary_address", nullable=False)
    op.alter_column("funds", "view_key", nullable=False)
    op.alter_column("funds", "start_height", nullable=False)

    # 4. Drop unique index and make deposit_address nullable again
    op.drop_index("ix_funds_deposit_address", table_name="funds")
    op.alter_column("funds", "deposit_address", nullable=True)

    # 5. Drop wallet_id columns
    op.drop_index("ix_posts_wallet_id", table_name="posts")
    op.drop_constraint("fk_posts_wallet_id", "posts", type="foreignkey")
    op.drop_column("posts", "wallet_id")

    op.drop_index("ix_transactions_wallet_id", table_name="transactions")
    op.drop_constraint("fk_transactions_wallet_id", "transactions", type="foreignkey")
    op.drop_column("transactions", "wallet_id")

    op.drop_index("ix_funds_wallet_id", table_name="funds")
    op.drop_constraint("fk_funds_wallet_id", "funds", type="foreignkey")
    op.drop_column("funds", "wallet_id")

    # 6. Drop wallets table
    op.drop_index("ix_wallets_uuid", table_name="wallets")
    op.drop_table("wallets")
