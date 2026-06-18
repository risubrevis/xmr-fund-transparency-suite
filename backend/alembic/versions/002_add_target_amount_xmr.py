"""Add target_amount_xmr column to funds table.

Revision ID: 002
Revises: 001
Create Date: 2026-06-19

"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"


def upgrade() -> None:
    op.add_column(
        "funds",
        sa.Column(
            "target_amount_xmr",
            sa.Numeric(precision=20, scale=12),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("funds", "target_amount_xmr")
