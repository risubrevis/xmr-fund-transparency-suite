"""posts: allow linking to a giveaway (fund_id nullable, add giveaway_id)

Revision ID: 011
Revises: 010
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make posts.fund_id nullable (a post may now belong to a giveaway instead).
    op.alter_column(
        "posts",
        "fund_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.add_column(
        "posts",
        sa.Column("giveaway_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_posts_giveaway_id",
        "posts",
        "giveaways",
        ["giveaway_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_posts_giveaway_id"), "posts", ["giveaway_id"])
    op.create_check_constraint(
        "post_fund_xor_giveaway",
        "posts",
        "(fund_id IS NOT NULL AND giveaway_id IS NULL) "
        "OR (fund_id IS NULL AND giveaway_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("post_fund_xor_giveaway", "posts", type_="check")
    op.drop_index(op.f("ix_posts_giveaway_id"), table_name="posts")
    op.drop_constraint("fk_posts_giveaway_id", "posts", type_="foreignkey")
    op.drop_column("posts", "giveaway_id")
    # Restore fund_id NOT NULL. This is only safe if no giveaway-linked posts
    # exist; alembic downgrade is intended for dev rollback.
    op.alter_column(
        "posts",
        "fund_id",
        existing_type=sa.UUID(),
        nullable=False,
    )