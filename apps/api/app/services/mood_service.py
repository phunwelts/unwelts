import hashlib
import hmac
import random
import uuid
from datetime import UTC, datetime, timedelta

import h3
from geoalchemy2 import WKTElement
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.enums import MoodType
from app.db.models.mood import Mood


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
    """
    std_dev = 0.005  # ~500 m at equator
    fuzzed_lat = max(-90.0, min(90.0, lat + random.gauss(0, std_dev)))
    fuzzed_lng = max(-180.0, min(180.0, lng + random.gauss(0, std_dev)))
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


async def check_and_set_rate_limit(redis: Redis, fingerprint: str) -> bool:
    """Return True if the submission is allowed, False if rate limited.

    Uses SET NX EXAT for an atomic check-and-set: a single Redis round-trip
    both checks existence and sets the key, eliminating any TOCTOU race.
    The key expires at UTC midnight so the limit resets predictably at day
    boundaries rather than rolling 24 h from first submission.
    """
    _, window_end = get_utc_day_window()
    expire_unix = int(window_end.timestamp())
    key = f"ratelimit:{fingerprint}"
    result: bool | None = await redis.set(key, 1, nx=True, exat=expire_unix)
    return result is not None


async def buffer_h3_aggregates(
    redis: Redis,
    h3_r5: str,
    h3_r7: str,
    mood_type: MoodType,
    window_start: datetime,
) -> None:
    """Buffer h3 aggregate increments in Redis instead of writing to Postgres directly.

    Under high concurrency, ON CONFLICT DO UPDATE on the same h3_aggregates row
    creates a write hotspot (classic DDIA hot-key problem). Redis atomic INCR
    decouples the write path: a background worker periodically flushes counters
    to Postgres in batches, eliminating row-level contention.

    Key format: h3agg:{YYYYMMDD}:{h3_cell}:{mood_type}:{resolution}
    TTL: 48 h after window_start to cover late-arriving flushes.
    """
    window_str = window_start.strftime("%Y%m%d")
    # TTL: window_start + 48 h to survive at least one flush cycle after window close
    expire_unix = int((window_start + timedelta(days=2)).timestamp())

    async with redis.pipeline(transaction=True) as pipe:
        for cell, resolution in ((h3_r5, 5), (h3_r7, 7)):
            key = f"h3agg:{window_str}:{cell}:{mood_type.value}:{resolution}"
            pipe.incr(key)
            pipe.expireat(key, expire_unix)
        await pipe.execute()
