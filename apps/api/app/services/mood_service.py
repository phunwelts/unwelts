import hashlib
import hmac
import json
import random
import re
import uuid
from datetime import UTC, datetime, timedelta

import h3
import sqlalchemy as sa
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_X, ST_Y
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.enums import MoodType
from app.db.models.h3_aggregate import H3Aggregate
from app.db.models.mood import Mood
from app.schemas.mood import RecentMoodItem

# Module-level SystemRandom instance: uses os.urandom() for each call,
# making coordinate fuzzing unpredictable even if the process state is leaked.
_rng = random.SystemRandom()

_HTML_TAG_RE = re.compile(r"<[^>]*>")
_NULL_BYTE_RE = re.compile(r"\x00")
_IP_RATE_LIMIT_MAX = 10  # requests per minute per IP


def sanitize_note(note: str | None) -> str | None:
    """Strip HTML tags and null bytes from user-supplied note text.

    Runs before DB insert so the database never stores raw HTML. We do not
    HTML-escape (that's the renderer's job); we strip tags entirely so the
    stored value is plain text.
    """
    if note is None:
        return None
    cleaned = _HTML_TAG_RE.sub("", note)
    cleaned = _NULL_BYTE_RE.sub("", cleaned)
    return cleaned.strip() or None


def compute_fingerprint(ip: str, user_agent: str) -> str:
    """HMAC-SHA256 fingerprint over ip+user_agent using the server secret.

    Using HMAC (not plain SHA-256) prevents reversibility: an attacker who
    observes a fingerprint cannot brute-force the input without the secret key.
    """
    message = f"{ip}:{user_agent}".encode()
    return hmac.new(
        settings.fingerprint_secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def fuzz_coordinates(lat: float, lng: float) -> tuple[float, float]:
    """Add gaussian noise (~500 m at equator) before persisting.

    Fuzzing happens here, before storage, so the database never holds
    the user's precise location. The stored point is already obfuscated.
    SystemRandom.gauss() delegates random() to os.urandom(), so the noise
    is OS-entropy-backed and cannot be predicted from process state alone.
    """
    std_dev = 0.005  # ~500 m at equator
    fuzzed_lat = max(-90.0, min(90.0, lat + _rng.gauss(0, std_dev)))
    fuzzed_lng = max(-180.0, min(180.0, lng + _rng.gauss(0, std_dev)))
    return fuzzed_lat, fuzzed_lng


def get_utc_day_window() -> tuple[datetime, datetime]:
    """Return (window_start, window_end) for the current UTC calendar day.

    Fixed UTC midnight windows simplify downstream analytical queries
    and avoid the complexity of rolling windows at read time.
    """
    now = datetime.now(UTC)
    window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(days=1)
    return window_start, window_end


async def insert_mood(
    session: AsyncSession,
    lat: float,
    lng: float,
    mood_type: MoodType,
    note: str | None,
    fingerprint: str,
) -> Mood:
    """Insert a mood row. Must be called inside an active session.begin() block.

    Fuzzing and H3 computation are applied to the fuzzed coordinates so that
    spatial cells are consistent with the stored geometry.
    submitted_at is set in Python (not server_default) so it is available
    immediately after flush without requiring a round-trip SELECT.
    """
    note = sanitize_note(note)
    fuzzed_lat, fuzzed_lng = fuzz_coordinates(lat, lng)

    # h3 4.x API: latlng_to_cell(lat, lng, resolution)
    h3_r5 = h3.latlng_to_cell(fuzzed_lat, fuzzed_lng, 5)
    h3_r7 = h3.latlng_to_cell(fuzzed_lat, fuzzed_lng, 7)

    # WKT uses (lng lat) — standard x/y axis order
    location = WKTElement(f"POINT({fuzzed_lng} {fuzzed_lat})", srid=4326)

    mood = Mood(
        id=uuid.uuid4(),
        fingerprint=fingerprint,
        mood_type=mood_type,
        note=note,
        location=location,
        h3_r5=h3_r5,
        h3_r7=h3_r7,
        submitted_at=datetime.now(UTC),
    )
    session.add(mood)
    return mood


async def upsert_h3_aggregates(
    session: AsyncSession,
    h3_r5: str,
    h3_r7: str,
    mood_type: MoodType,
    window_start: datetime,
    window_end: datetime,
) -> None:
    """Upsert h3 aggregate counts for both H3 resolutions in the same transaction.

    Runs inside the same session.begin() as insert_mood, so mood insertion and
    aggregate update are atomic: no partial writes possible. ON CONFLICT DO UPDATE
    is safe at MVP scale; for high-volume Phase 6, migrate to Redis write buffer.
    """
    for cell, resolution in ((h3_r5, 5), (h3_r7, 7)):
        stmt = (
            pg_insert(H3Aggregate)
            .values(
                id=uuid.uuid4(),
                h3_cell=cell,
                resolution=resolution,
                mood_type=mood_type,
                count=1,
                window_start=window_start,
                window_end=window_end,
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_update(
                constraint="uq_h3_aggregates",
                set_={
                    "count": H3Aggregate.__table__.c.count + 1,
                    "updated_at": sa.func.now(),
                },
            )
        )
        await session.execute(stmt)


# ---------------------------------------------------------------------------
# Phase 6 reference: Redis write buffer for h3_aggregates
#
# Under high concurrency, ON CONFLICT DO UPDATE on the same h3_aggregates row
# creates a write hotspot (classic DDIA hot-key problem). Redis atomic INCR
# decouples the write path: a background worker periodically flushes counters
# to Postgres in batches, eliminating row-level contention.
#
# Key format: h3agg:{YYYYMMDD}:{h3_cell}:{mood_type}:{resolution}
# TTL: 48 h after window_start to cover late-arriving flushes.
#
# async def buffer_h3_aggregates(
#     redis: Redis,
#     h3_r5: str,
#     h3_r7: str,
#     mood_type: MoodType,
#     window_start: datetime,
# ) -> None:
#     window_str = window_start.strftime("%Y%m%d")
#     expire_unix = int((window_start + timedelta(days=2)).timestamp())
#     async with redis.pipeline(transaction=True) as pipe:
#         for cell, resolution in ((h3_r5, 5), (h3_r7, 7)):
#             key = f"h3agg:{window_str}:{cell}:{mood_type.value}:{resolution}"
#             pipe.incr(key)
#             pipe.expireat(key, expire_unix)
#         await pipe.execute()
# ---------------------------------------------------------------------------


async def check_and_set_rate_limit(redis: Redis, fingerprint: str) -> int | None:
    """Return None if allowed, or TTL seconds remaining if rate limited.

    Uses SET NX EX for an atomic check-and-set: a single Redis round-trip
    both checks existence and sets the key, eliminating any TOCTOU race.
    The TTL is a rolling window controlled by RATE_LIMIT_WINDOW_HOURS (default 4 h),
    making it easy to shorten for testing or staging without code changes.
    When rate limited, a second round-trip fetches the remaining TTL so the
    frontend can show an accurate "try again in Xh Ym" message.
    """
    window_seconds = settings.rate_limit_window_hours * 3600
    key = f"ratelimit:{fingerprint}"
    result: bool | None = await redis.set(key, 1, nx=True, ex=window_seconds)
    if result is not None:
        return None  # allowed
    ttl: int = await redis.ttl(key)
    return max(ttl, 0)


async def check_ip_rate_limit(redis: Redis, ip: str) -> bool:
    """Return True if the IP is within the per-minute request limit, False otherwise.

    Uses a fixed-window counter keyed by IP + UTC minute bucket. The key TTL is
    set to 90 s (1.5x the window) to guarantee the counter outlives its bucket
    regardless of sub-second timing. INCR is atomic, so no TOCTOU race exists.
    """
    minute_bucket = int(datetime.now(UTC).timestamp()) // 60
    key = f"ip_ratelimit:{ip}:{minute_bucket}"
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, 90)
        results = await pipe.execute()
    count: int = results[0]
    return count <= _IP_RATE_LIMIT_MAX


_RECENT_MOODS_TTL = 15  # seconds


async def get_recent_moods(
    session: AsyncSession,
    redis: Redis,
    limit: int,
) -> tuple[list[RecentMoodItem], int]:
    """Return the most recent mood submissions and today's total signal count.

    Cache-aside with TTL 15 s: serves repeated polling from Redis instead of
    hitting Postgres on every 30 s frontend tick. Invalidated on POST /moods.
    Coordinates are extracted from the PostGIS geometry via ST_X/ST_Y so the
    caller receives plain floats without any GeoAlchemy2 wrapper types.
    City is not yet populated (reserved for future reverse-geocoding).
    """
    cache_key = f"moods:recent:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        return [RecentMoodItem.model_validate(d) for d in data["moods"]], data["total"]

    stmt = (
        select(
            Mood.id,
            Mood.mood_type,
            Mood.note,
            ST_Y(Mood.location).label("lat"),
            ST_X(Mood.location).label("lng"),
            Mood.submitted_at,
        )
        .order_by(Mood.submitted_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    items = [
        RecentMoodItem(
            id=row.id,
            mood_type=row.mood_type,
            note=row.note,
            lat=float(row.lat),
            lng=float(row.lng),
            submitted_at=row.submitted_at,
        )
        for row in result.all()
    ]

    window_start, _ = get_utc_day_window()
    total_stmt = select(sa.func.count()).select_from(Mood).where(
        Mood.submitted_at >= window_start
    )
    total: int = (await session.execute(total_stmt)).scalar_one()

    payload = json.dumps(
        {"moods": [item.model_dump(mode="json") for item in items], "total": total}
    )
    await redis.set(cache_key, payload, ex=_RECENT_MOODS_TTL)
    return items, total
