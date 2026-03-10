from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DBSession
from app.schemas.map import MapResponse
from app.services import map_service

router = APIRouter()


@router.get("/map", response_model=MapResponse)
async def get_map(
    session: DBSession,
    resolution: Annotated[
        int,
        Query(description="H3 resolution: 5 (city-level) or 7 (neighbourhood-level)"),
    ] = 5,
    date: Annotated[
        str | None,
        Query(description="UTC date in YYYY-MM-DD format. Defaults to today."),
    ] = None,
) -> MapResponse:
    if resolution not in (5, 7):
        raise HTTPException(status_code=422, detail="resolution must be 5 or 7")

    if date is not None:
        try:
            window_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail="date must be in YYYY-MM-DD format"
            ) from exc
    else:
        now = datetime.now(UTC)
        window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return await map_service.get_map_data(
        session=session,
        resolution=resolution,
        window_start=window_start,
    )
