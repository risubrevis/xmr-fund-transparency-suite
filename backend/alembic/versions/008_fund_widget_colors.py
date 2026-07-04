"""Add per-fund widget background and text color fields.

Each fund can now override the global widget colors with its own
widget_background_color and widget_text_color.

Revision ID: 008
Revises: 007
Create Date: 2026-07-02

"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column("widget_background_color", sa.String(7), nullable=True),
    )
    op.add_column(
        "funds",
        sa.Column("widget_text_color", sa.String(7), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("funds", "widget_text_color")
    op.drop_column("funds", "widget_background_color")
