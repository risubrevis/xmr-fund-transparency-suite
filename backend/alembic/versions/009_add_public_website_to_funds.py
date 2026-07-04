"""add public_website to funds

Revision ID: 009_add_public_website
Revises: 008_fund_widget_colors
Create Date: 2026-07-02
"""

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column("public_website", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("funds", "public_website")
