from fastapi import APIRouter, Request

from app.api.deps import DBSession, RedisClient
from app.schemas.mood import MoodResponse, MoodSubmitRequest
from app.services import mood_service
from app.services.mood_service import get_utc_day_window

router = APIRouter()


@router.post("/moods", response_model=MoodResponse, status_code=201)
async def submit_mood(
    request: Request,
    body: MoodSubmitRequest,
    session: DBSession,
    redis: RedisClient,
) -> MoodResponse:
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    fingerprint = mood_service.compute_fingerprint(ip, user_agent)

    async with session.begin():
        mood = await mood_service.insert_mood(
            session=session,
            lat=body.lat,
            lng=body.lng,
            mood_type=body.mood_type,
            note=body.note,
            fingerprint=fingerprint,
        )

    # Redis buffer happens after the DB transaction commits.
    # If Redis is temporarily unavailable, the mood is already durably persisted
    # and the aggregate can be rebuilt from the moods table.
    window_start, _ = get_utc_day_window()
    await mood_service.buffer_h3_aggregates(
        redis=redis,
        h3_r5=mood.h3_r5,
        h3_r7=mood.h3_r7,
        mood_type=mood.mood_type,
        window_start=window_start,
    )

    return MoodResponse(
        id=mood.id,
        mood_type=mood.mood_type,
        submitted_at=mood.submitted_at,
    )
