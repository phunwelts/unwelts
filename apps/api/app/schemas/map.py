from typing import Literal

from pydantic import BaseModel

from app.db.models.enums import MoodType


class MoodCounts(BaseModel):
    happy: int = 0
    sad: int = 0
    anxious: int = 0
    angry: int = 0
    calm: int = 0
    tired: int = 0


class HexProperties(BaseModel):
    h3_cell: str
    dominant_mood: MoodType
    moods: MoodCounts
    total: int


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]


class HexFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PolygonGeometry
    properties: HexProperties


class MapResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[HexFeature]
