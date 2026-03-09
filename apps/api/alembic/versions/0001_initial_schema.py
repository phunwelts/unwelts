"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-09 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MOOD_TYPE_VALUES = ("happy", "sad", "anxious", "angry", "excited", "calm", "tired")


def upgrade() -> None:
    # --- Extensions ---
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # --- Enum (idempotent) ---
    mood_values = "('happy','sad','anxious','angry','excited','calm','tired')"
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE mood_type AS ENUM {mood_values};
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # --- moods ---
    op.create_table(
        "moods",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "mood_type",
            postgresql.ENUM(*_MOOD_TYPE_VALUES, name="mood_type", create_type=False),
            nullable=False,
        ),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=False),
        sa.Column("h3_r5", sa.String(15), nullable=False),
        sa.Column("h3_r7", sa.String(15), nullable=False),
        sa.Column(
            "submitted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index("ix_moods_fingerprint", "moods", ["fingerprint"])
    op.create_index("ix_moods_submitted_at", "moods", ["submitted_at"])
    op.create_index("ix_moods_h3_r5", "moods", ["h3_r5"])
    op.create_index("ix_moods_h3_r7", "moods", ["h3_r7"])
    # GIST index for spatial queries — requires raw SQL
    op.execute("CREATE INDEX ix_moods_location ON moods USING GIST (location)")

    # --- h3_aggregates ---
    op.create_table(
        "h3_aggregates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("h3_cell", sa.String(15), nullable=False),
        sa.Column("resolution", sa.SmallInteger, nullable=False),
        sa.Column(
            "mood_type",
            postgresql.ENUM(*_MOOD_TYPE_VALUES, name="mood_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "count", sa.Integer, nullable=False, server_default=sa.text("0")
        ),
        sa.Column("window_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("window_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint(
            "h3_cell", "mood_type", "window_start", name="uq_h3_aggregates"
        ),
    )

    op.create_index("ix_h3_aggregates_h3_cell", "h3_aggregates", ["h3_cell"])
    op.create_index(
        "ix_h3_aggregates_window_start", "h3_aggregates", ["window_start"]
    )


def downgrade() -> None:
    op.drop_table("h3_aggregates")
    op.drop_table("moods")
    op.execute("DROP TYPE IF EXISTS mood_type")
    # PostGIS extension kept intentionally — removing it would destroy all geometry data
