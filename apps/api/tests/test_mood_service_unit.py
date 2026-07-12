import asyncio
from datetime import UTC, datetime, timedelta

import h3
import pytest
import sqlalchemy as sa
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.enums import MoodType
from app.db.models.h3_aggregate import H3Aggregate
from app.services.mood_service import (
    _IP_RATE_LIMIT_MAX,
    check_and_set_rate_limit,
    check_ip_rate_limit,
    compute_fingerprint,
    fuzz_coordinates,
    get_utc_day_window,
    sanitize_note,
    upsert_h3_aggregates,
)

# ---------------------------------------------------------------------------
# sanitize_note
# ---------------------------------------------------------------------------


def test_sanitize_none_passes_through() -> None:
    assert sanitize_note(None) is None


def test_sanitize_plain_text_untouched() -> None:
    assert sanitize_note("feeling great today") == "feeling great today"


def test_sanitize_strips_html_tags_keeps_content() -> None:
    assert sanitize_note("<b>hi</b> there") == "hi there"


def test_sanitize_strips_script_tags() -> None:
    assert sanitize_note("<script>alert(1)</script>ok") == "alert(1)ok"


def test_sanitize_strips_null_bytes() -> None:
    assert sanitize_note("a\x00b") == "ab"


def test_sanitize_whitespace_only_becomes_none() -> None:
    assert sanitize_note("   ") is None


def test_sanitize_tags_only_becomes_none() -> None:
    assert sanitize_note("<div><br/></div>") is None


# ---------------------------------------------------------------------------
# compute_fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_is_deterministic_hex_sha256() -> None:
    fp1 = compute_fingerprint("1.2.3.4", "test-agent")
    fp2 = compute_fingerprint("1.2.3.4", "test-agent")
    assert fp1 == fp2
    assert len(fp1) == 64
    int(fp1, 16)  # valid hex


def test_fingerprint_changes_with_ip() -> None:
    assert compute_fingerprint("1.2.3.4", "ua") != compute_fingerprint(
        "1.2.3.5", "ua"
    )


def test_fingerprint_changes_with_user_agent() -> None:
    assert compute_fingerprint("1.2.3.4", "ua-a") != compute_fingerprint(
        "1.2.3.4", "ua-b"
    )


def test_fingerprint_changes_with_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    fp_before = compute_fingerprint("1.2.3.4", "ua")
    monkeypatch.setattr(settings, "fingerprint_secret", "x" * 32)
    fp_after = compute_fingerprint("1.2.3.4", "ua")
    assert fp_before != fp_after


# ---------------------------------------------------------------------------
# fuzz_coordinates / get_utc_day_window
# ---------------------------------------------------------------------------


def test_fuzz_stays_near_input_and_in_bounds() -> None:
    lat, lng = fuzz_coordinates(40.7128, -74.0060)
    # std dev is 0.005; 0.05 is 10 sigma — effectively impossible to exceed
    assert abs(lat - 40.7128) < 0.05
    assert abs(lng - -74.0060) < 0.05


def test_fuzz_clamps_at_world_edges() -> None:
    lat, lng = fuzz_coordinates(90.0, 180.0)
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lng <= 180.0


def test_fuzz_is_nondeterministic() -> None:
    assert fuzz_coordinates(10.0, 10.0) != fuzz_coordinates(10.0, 10.0)


def test_utc_day_window_is_midnight_aligned_single_day() -> None:
    start, end = get_utc_day_window()
    assert start.tzinfo == UTC
    assert (start.hour, start.minute, start.second, start.microsecond) == (0, 0, 0, 0)
    assert end - start == timedelta(days=1)


# ---------------------------------------------------------------------------
# Fingerprint rate limit (Redis)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fingerprint_limit_allows_first_blocks_second(redis: Redis) -> None:
    assert await check_and_set_rate_limit(redis, "fp-1") is None

    ttl = await check_and_set_rate_limit(redis, "fp-1")
    assert ttl is not None
    assert 0 < ttl <= settings.rate_limit_window_hours * 3600


@pytest.mark.asyncio
async def test_fingerprint_limit_is_per_fingerprint(redis: Redis) -> None:
    assert await check_and_set_rate_limit(redis, "fp-a") is None
    assert await check_and_set_rate_limit(redis, "fp-b") is None


# ---------------------------------------------------------------------------
# IP rate limit (Redis)
# ---------------------------------------------------------------------------


async def _avoid_minute_boundary() -> None:
    """The IP limiter uses fixed minute buckets; don't let the test straddle one."""
    now = datetime.now(UTC)
    if now.second >= 55:
        await asyncio.sleep(60 - now.second)


@pytest.mark.asyncio
async def test_ip_limit_blocks_after_max_requests(redis: Redis) -> None:
    await _avoid_minute_boundary()
    for _ in range(_IP_RATE_LIMIT_MAX):
        assert await check_ip_rate_limit(redis, "9.9.9.9") is True
    assert await check_ip_rate_limit(redis, "9.9.9.9") is False


@pytest.mark.asyncio
async def test_ip_limit_is_per_ip(redis: Redis) -> None:
    await _avoid_minute_boundary()
    for _ in range(_IP_RATE_LIMIT_MAX + 1):
        await check_ip_rate_limit(redis, "9.9.9.9")
    assert await check_ip_rate_limit(redis, "8.8.8.8") is True


# ---------------------------------------------------------------------------
# H3 aggregate upsert (Postgres)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_increments_existing_row(db_session: AsyncSession) -> None:
    cell_r5 = h3.latlng_to_cell(40.7128, -74.0060, 5)
    cell_r7 = h3.latlng_to_cell(40.7128, -74.0060, 7)
    window_start, window_end = get_utc_day_window()

    async with db_session.begin():
        for _ in range(2):
            await upsert_h3_aggregates(
                session=db_session,
                h3_r5=cell_r5,
                h3_r7=cell_r7,
                mood_type=MoodType.happy,
                window_start=window_start,
                window_end=window_end,
            )

    rows = (
        await db_session.execute(
            sa.select(
                H3Aggregate.h3_cell,
                H3Aggregate.resolution,
                # labeled: bare .count on a Row is shadowed by tuple.count
                H3Aggregate.count.label("n"),
            ).order_by(H3Aggregate.resolution)
        )
    ).all()
    assert [(r.h3_cell, r.resolution, r.n) for r in rows] == [
        (cell_r5, 5, 2),
        (cell_r7, 7, 2),
    ]


@pytest.mark.asyncio
async def test_upsert_separates_mood_types(db_session: AsyncSession) -> None:
    cell_r5 = h3.latlng_to_cell(40.7128, -74.0060, 5)
    cell_r7 = h3.latlng_to_cell(40.7128, -74.0060, 7)
    window_start, window_end = get_utc_day_window()

    async with db_session.begin():
        for mood in (MoodType.happy, MoodType.sad):
            await upsert_h3_aggregates(
                session=db_session,
                h3_r5=cell_r5,
                h3_r7=cell_r7,
                mood_type=mood,
                window_start=window_start,
                window_end=window_end,
            )

    counts = (
        (
            await db_session.execute(
                sa.select(sa.func.count()).select_from(H3Aggregate)
            )
        ).scalar_one(),
    )
    assert counts == (4,)  # 2 moods x 2 resolutions, each its own row with count 1
