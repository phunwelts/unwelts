import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base
from app.db.models.enums import MoodType


class Mood(Base):
    __tablename__ = "moods"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fingerprint: Mapped[str] = mapped_column(sa.String(64), index=True)
    mood_type: Mapped[MoodType] = mapped_column(sa.Enum(MoodType, name="mood_type"))
    note: Mapped[str | None] = mapped_column(sa.Text)
    location: Mapped[Any] = mapped_column(Geometry("POINT", srid=4326))
    h3_r5: Mapped[str] = mapped_column(sa.String(15), index=True)
    h3_r7: Mapped[str] = mapped_column(sa.String(15), index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
