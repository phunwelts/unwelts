from datetime import datetime

import h3
import sqlalchemy as sa
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import MoodType
from app.db.models.h3_aggregate import H3Aggregate
from app.schemas.map import (
    HexFeature,
    HexProperties,
    MapResponse,
    MoodCounts,
    PolygonGeometry,
)

_MAP_TTL = 30  # seconds


def _cell_to_geojson_polygon(cell: str) -> PolygonGeometry:
    """Convert an H3 cell to a GeoJSON Polygon geometry.

    h3.cell_to_boundary() returns [(lat, lng), ...].
    GeoJSON requires [lng, lat] (x/y) order and a closed ring (first == last).
    """
    boundary = h3.cell_to_boundary(cell)
    coords: list[list[float]] = [[lng, lat] for lat, lng in boundary]
    coords.append(coords[0])
    return PolygonGeometry(coordinates=[coords])


async def get_map_data(
    session: AsyncSession,
    redis: Redis,
    resolution: int,
    window_start: datetime,
) -> MapResponse:
    """Query h3_aggregates for the given resolution and day window.

    Cache-aside with TTL 30 s: the heatmap query is expensive (full table scan
    on h3_aggregates) and the data changes only on POST /moods. Invalidated on
    every successful mood submission. Groups rows by h3_cell, sums counts per
    mood_type, and returns a GeoJSON FeatureCollection.
    """
    cache_key = f"map:{resolution}:{window_start.strftime('%Y-%m-%d')}"
    cached = await redis.get(cache_key)
    if cached:
        return MapResponse.model_validate_json(cached)

    result = await session.execute(
        sa.select(
            H3Aggregate.h3_cell,
            H3Aggregate.mood_type,
            sa.func.sum(H3Aggregate.count).label("total"),
        )
        .where(
            H3Aggregate.resolution == resolution,
            H3Aggregate.window_start == window_start,
        )
        .group_by(H3Aggregate.h3_cell, H3Aggregate.mood_type)
    )
    rows = result.all()

    # Aggregate counts per cell
    cells: dict[str, dict[MoodType, int]] = {}
    for row in rows:
        cell: str = row.h3_cell
        if cell not in cells:
            cells[cell] = {}
        cells[cell][row.mood_type] = int(row.total)

    features: list[HexFeature] = []
    for cell, mood_counts in cells.items():
        dominant = max(mood_counts, key=lambda m: mood_counts[m])
        total = sum(mood_counts.values())
        moods = MoodCounts(**{m.value: c for m, c in mood_counts.items()})
        features.append(
            HexFeature(
                geometry=_cell_to_geojson_polygon(cell),
                properties=HexProperties(
                    h3_cell=cell,
                    dominant_mood=dominant,
                    moods=moods,
                    total=total,
                ),
            )
        )

    response = MapResponse(features=features)
    await redis.set(cache_key, response.model_dump_json(), ex=_MAP_TTL)
    return response
