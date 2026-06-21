"""Add fund_id foreign key to posts table.

Revision ID: 006
Revises: 005
Create Date: 2026-06-22

"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"


def upgrade() -> None:
    op.add_column(
        "posts",
        sa.Column("fund_id", sa.UUID(), nullable=True),
    )

    # Populate fund_id for existing rows from the single fund in this instance
    op.execute("UPDATE posts SET fund_id = (SELECT id FROM funds LIMIT 1)")

    op.alter_column("posts", "fund_id", nullable=False)
    op.create_foreign_key(
        "fk_posts_fund_id",
        "posts",
        "funds",
        ["fund_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_posts_fund_id", "posts", ["fund_id"])


def downgrade() -> None:
    op.drop_index("ix_posts_fund_id", table_name="posts")
    op.drop_constraint("fk_posts_fund_id", "posts", type_="foreignkey")
    op.drop_column("posts", "fund_id")
