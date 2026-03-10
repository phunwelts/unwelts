import sqlalchemy as sa
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import DBSession, RedisClient

router = APIRouter()


@router.get("/health")
async def health_check(session: DBSession, redis: RedisClient) -> JSONResponse:
    db_status = "ok"
    redis_status = "ok"

    try:
        await session.execute(sa.text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        await redis.ping()  # type: ignore[misc]
    except Exception:
        redis_status = "error"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    status_code = 200 if overall == "ok" else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "db": db_status, "redis": redis_status},
    )
