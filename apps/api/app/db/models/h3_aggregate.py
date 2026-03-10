import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base
from app.db.models.enums import MoodType


class H3Aggregate(Base):
    __tablename__ = "h3_aggregates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    h3_cell: Mapped[str] = mapped_column(sa.String(15), index=True)
    resolution: Mapped[int] = mapped_column(sa.SmallInteger)
    mood_type: Mapped[MoodType] = mapped_column(
        sa.Enum(MoodType, name="mood_type", create_constraint=False)
    )
    count: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("0"))
    window_start: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), index=True
    )
    window_end: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "h3_cell", "mood_type", "window_start", name="uq_h3_aggregates"
        ),
    )
