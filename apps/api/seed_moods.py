"""
Seed script — inserts mock moods directly into the DB, bypassing rate limit.
Each anchor city also spawns a random nearby cluster, yielding ~200+ signals
around the world with staggered recent timestamps.

Run with: docker compose exec api python seed_moods.py [--fresh]
  --fresh: wipe moods + h3_aggregates first, so the world is exactly the seed.
"""
import asyncio
import os
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import h3

# (lat, lng, mood_type, note)
POINTS = [
    # South America
    (-23.55, -46.63, "happy",   "good news today"),      # São Paulo
    (-22.90, -43.17, "calm",    None),                   # Rio de Janeiro
    (-34.60, -58.38, "anxious", None),                   # Buenos Aires
    (-33.45, -70.66, "tired",   None),                   # Santiago
    (  4.71, -74.07, "angry",   None),                   # Bogotá
    # North America
    ( 40.71, -74.00, "anxious", "exam season"),          # New York
    ( 41.87, -87.62, "sad",     None),                   # Chicago
    ( 34.05,-118.24, "happy",   None),                   # Los Angeles
    ( 19.43, -99.13, "calm",    None),                   # Mexico City
    ( 43.65, -79.38, "tired",   "another late night"),   # Toronto
    # Europe
    ( 51.50,  -0.12, "sad",     None),                   # London
    ( 48.85,   2.35, "calm",    None),                   # Paris
    ( 52.52,  13.40, "anxious", "job market pressure"),  # Berlin
    ( 40.41,  -3.70, "happy",   None),                   # Madrid
    ( 41.90,  12.49, "calm",    None),                   # Rome
    ( 59.91,  10.75, "tired",   None),                   # Oslo
    ( 55.75,  37.61, "angry",   None),                   # Moscow
    ( 41.01,  28.97, "anxious", None),                   # Istanbul
    # Africa & Middle East
    ( 30.04,  31.23, "sad",     None),                   # Cairo
    (  6.52,   3.38, "happy",   "community event"),      # Lagos
    ( -1.29,  36.82, "happy",   None),                   # Nairobi
    (-26.20,  28.04, "calm",    None),                   # Johannesburg
    ( 25.20,  55.27, "anxious", "heat wave"),            # Dubai
    # Asia & Pacific
    ( 28.61,  77.20, "anxious", None),                   # New Delhi
    ( 19.07,  72.87, "tired",   None),                   # Mumbai
    ( 35.68, 139.69, "tired",   "another late night"),   # Tokyo
    ( 39.90, 116.40, "calm",    None),                   # Beijing
    (  1.35, 103.81, "happy",   None),                   # Singapore
    (-33.86, 151.20, "angry",   None),                   # Sydney
    ( 37.56, 126.97, "anxious", "exam season"),          # Seoul
]

MOOD_TYPES = ["happy", "calm", "anxious", "sad", "angry", "tired"]

# Occasional notes for cluster signals (most carry none, like real traffic).
CLUSTER_NOTES = [
    "long day", "small win today", "can't sleep", "monday feelings",
    "sun is out", "traffic again", "quiet evening", "deadline week",
    "coffee helped", "missing home", "new beginnings", "rain all day",
]

CLUSTER_MIN, CLUSTER_MAX = 5, 9   # extra signals per anchor city
JITTER_DEG = 0.35                 # ~30-40 km scatter around the anchor
MAX_AGE_HOURS = 6                 # timestamps spread over the recent past

SQL = """
    INSERT INTO moods
        (id, fingerprint, mood_type, note, location, h3_r5, h3_r7, submitted_at)
    VALUES
        ($1, $2, $3::mood_type, $4,
         ST_SetSRID(ST_MakePoint($6, $5), 4326), $7, $8, $9)
"""


async def insert_mood(
    conn: asyncpg.Connection,
    lat: float,
    lng: float,
    mood_type: str,
    note: str | None,
    submitted: datetime,
) -> None:
    await conn.execute(
        SQL,
        uuid.uuid4(), f"seed-{uuid.uuid4().hex}", mood_type, note,
        lat, lng,
        h3.latlng_to_cell(lat, lng, 5), h3.latlng_to_cell(lat, lng, 7),
        submitted,
    )


async def main() -> None:
    if os.environ.get("APP_ENV") == "production":
        raise SystemExit("seed_moods.py must not run in production.")

    raw_url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    conn = await asyncpg.connect(raw_url)

    if "--fresh" in sys.argv:
        await conn.execute("DELETE FROM moods")
        await conn.execute("DELETE FROM h3_aggregates")
        print("· wiped existing moods + aggregates")

    now = datetime.now(UTC)
    inserted = 0

    for lat, lng, mood_type, note in POINTS:
        # The anchor city signal, with its curated note.
        await insert_mood(
            conn, lat, lng, mood_type, note,
            now - timedelta(minutes=random.uniform(0, MAX_AGE_HOURS * 60)),
        )
        inserted += 1

        # A cluster of random signals scattered around it. The anchor's mood
        # is weighted 3x so each region keeps a loose dominant color.
        weights = [3 if m == mood_type else 1 for m in MOOD_TYPES]
        for _ in range(random.randint(CLUSTER_MIN, CLUSTER_MAX)):
            await insert_mood(
                conn,
                max(-90.0, min(90.0, lat + random.gauss(0, JITTER_DEG))),
                max(-180.0, min(180.0, lng + random.gauss(0, JITTER_DEG))),
                random.choices(MOOD_TYPES, weights=weights)[0],
                random.choice(CLUSTER_NOTES) if random.random() < 0.15 else None,
                now - timedelta(minutes=random.uniform(0, MAX_AGE_HOURS * 60)),
            )
            inserted += 1

    await conn.close()
    print(f"✓ {inserted} moods inserted across {len(POINTS)} regions.")


if __name__ == "__main__":
    asyncio.run(main())
