"""
Cluster stress test — inserts N points concentrated in a region with random jitter.
Run with: docker-compose run --rm api python seed_cluster.py
"""
import asyncio
import os
import random
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import h3

# Center + spread (degrees) + mood distribution
CLUSTERS = [
    # (center_lat, center_lng, spread_deg, n, moods)
    (48.8,   8.0,  4.0, 40, ["happy", "calm", "tired"]),   # Europe (Central)
    (35.7, 139.7,  1.5, 30, ["tired", "anxious", "calm"]), # Tokyo metro
    (40.7,  -74.0, 2.0, 30, ["anxious", "sad", "angry"]),  # New York area
]

SQL = """
    INSERT INTO moods
        (id, fingerprint, mood_type, note, location, h3_r5, h3_r7, submitted_at)
    VALUES
        ($1, $2, $3::mood_type, $4,
         ST_SetSRID(ST_MakePoint($6, $5), 4326), $7, $8, $9)
"""


async def main() -> None:
    if os.environ.get("APP_ENV") == "production":
        raise SystemExit("seed_cluster.py must not run in production.")

    raw_url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    conn = await asyncpg.connect(raw_url)
    rng = random.SystemRandom()
    now = datetime.now(UTC)
    inserted = 0

    for center_lat, center_lng, spread, n, moods in CLUSTERS:
        for _ in range(n):
            lat = center_lat + rng.uniform(-spread, spread)
            lng = center_lng + rng.uniform(-spread, spread)
            mood = rng.choice(moods)
            mood_id   = uuid.uuid4()
            fp        = f"cluster-{uuid.uuid4().hex}"
            h3_r5     = h3.latlng_to_cell(lat, lng, 5)
            h3_r7     = h3.latlng_to_cell(lat, lng, 7)
            submitted = now - timedelta(seconds=inserted * 10)

            await conn.execute(
                SQL,
                mood_id, fp, mood, None,
                lat, lng, h3_r5, h3_r7, submitted,
            )
            inserted += 1

    await conn.close()
    print(f"✓ {inserted} clustered moods inserted.")


if __name__ == "__main__":
    asyncio.run(main())
