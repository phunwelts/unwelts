import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import MoodType


class MoodSubmitRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    mood_type: MoodType
    note: str | None = Field(None, max_length=500)


class MoodResponse(BaseModel):
    id: uuid.UUID
    mood_type: MoodType
    submitted_at: datetime

    model_config = {"from_attributes": True}
