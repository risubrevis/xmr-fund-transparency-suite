"""Add posts table for news/announcements.

Revision ID: 005
Revises: 004
Create Date: 2026-06-22

"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("body", sa.String(2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("posts")
