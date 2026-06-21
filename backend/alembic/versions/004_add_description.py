"""Add description column to funds table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-21

"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column(
            "description",
            sa.String(2048),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("funds", "description")
