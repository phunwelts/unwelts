"""h3_aggregates composite index on (resolution, window_start)

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-11 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Composite index to speed up GET /map queries that filter by resolution
    # and window_start (current UTC day). The existing ix_h3_aggregates_window_start
    # single-column index is not dropped — it remains useful for window-only scans.
    op.create_index(
        "ix_h3_aggregates_resolution_window_start",
        "h3_aggregates",
        ["resolution", "window_start"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_h3_aggregates_resolution_window_start",
        table_name="h3_aggregates",
    )
