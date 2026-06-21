"""Add deposit_address column to funds table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-21

"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column(
            "deposit_address",
            sa.String(95),
            nullable=True,
        ),
    )
    # Populate deposit_address with primary_address for existing rows
    op.execute(
        "UPDATE funds SET deposit_address = primary_address WHERE deposit_address IS NULL"
    )


def downgrade() -> None:
    op.drop_column("funds", "deposit_address")
