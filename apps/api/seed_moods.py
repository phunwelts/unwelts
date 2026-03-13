"""
Seed script — inserts mock moods directly into the DB, bypassing rate limit.
Run with: docker-compose run --rm api python seed_moods.py
"""
import asyncio
import os
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

SQL = """
    INSERT INTO moods
        (id, fingerprint, mood_type, note, location, h3_r5, h3_r7, submitted_at)
    VALUES
        ($1, $2, $3::mood_type, $4,
         ST_SetSRID(ST_MakePoint($6, $5), 4326), $7, $8, $9)
"""


async def main() -> None:
    raw_url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    conn = await asyncpg.connect(raw_url)

    now = datetime.now(UTC)
    inserted = 0

    for i, (lat, lng, mood_type, note) in enumerate(POINTS):
        mood_id   = uuid.uuid4()
        fp        = f"seed-{uuid.uuid4().hex}"
        h3_r5     = h3.latlng_to_cell(lat, lng, 5)
        h3_r7     = h3.latlng_to_cell(lat, lng, 7)
        submitted = now - timedelta(seconds=i * 30)

        await conn.execute(
            SQL,
            mood_id, fp, mood_type, note,
            lat, lng,
            h3_r5, h3_r7, submitted,
        )
        inserted += 1
        print(f"  [{i+1:02d}/{len(POINTS)}] {mood_type:8s}  {lat:7.2f}, {lng:8.2f}")

    await conn.close()
    print(f"\n✓ {inserted} moods inserted.")


if __name__ == "__main__":
    asyncio.run(main())
