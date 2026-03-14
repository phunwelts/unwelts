from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.deps import DBSession, RedisClient
from app.schemas.mood import MoodResponse, MoodSubmitRequest, RecentMoodsResponse
from app.services import mood_service
from app.services.mood_service import get_utc_day_window

router = APIRouter()


def _extract_ip(request: Request) -> str:
    """Return the real client IP, preferring X-Forwarded-For when behind a proxy."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/moods", response_model=MoodResponse, status_code=201)
async def submit_mood(
    request: Request,
    body: MoodSubmitRequest,
    session: DBSession,
    redis: RedisClient,
) -> MoodResponse:
    ip = _extract_ip(request)
    user_agent = request.headers.get("user-agent", "")

    ip_allowed = await mood_service.check_ip_rate_limit(redis, ip)
    if not ip_allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down.",
        )

    fingerprint = mood_service.compute_fingerprint(ip, user_agent)

    allowed = await mood_service.check_and_set_rate_limit(redis, fingerprint)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="You have already submitted a mood today. Try again tomorrow.",
        )

    window_start, window_end = get_utc_day_window()
    async with session.begin():
        mood = await mood_service.insert_mood(
            session=session,
            lat=body.lat,
            lng=body.lng,
            mood_type=body.mood_type,
            note=body.note,
            fingerprint=fingerprint,
        )
        await mood_service.upsert_h3_aggregates(
            session=session,
            h3_r5=mood.h3_r5,
            h3_r7=mood.h3_r7,
            mood_type=mood.mood_type,
            window_start=window_start,
            window_end=window_end,
        )

    return MoodResponse(
        id=mood.id,
        mood_type=mood.mood_type,
        submitted_at=mood.submitted_at,
    )


@router.get("/moods/recent", response_model=RecentMoodsResponse)
async def get_recent_moods(
    session: DBSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RecentMoodsResponse:
    moods = await mood_service.get_recent_moods(session, limit)
    return RecentMoodsResponse(moods=moods)
