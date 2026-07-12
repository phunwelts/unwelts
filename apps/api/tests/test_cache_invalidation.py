import pytest
from httpx import AsyncClient

VALID_PAYLOAD = {"lat": 40.7128, "lng": -74.0060, "mood_type": "happy"}

# POST /moods invalidates exactly these cache keys (see submit_mood):
# moods:recent:100 and map:{5,7}:{today}. A second submission from the same
# client would hit the fingerprint rate limit, so each POST uses a distinct
# User-Agent to produce a distinct fingerprint (same IP stays under the
# 10/min IP limit).


@pytest.mark.asyncio
async def test_recent_moods_cache_invalidated_on_submit(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/moods", json=VALID_PAYLOAD, headers={"user-agent": "ua-1"}
    )
    assert r.status_code == 201

    first = await client.get("/api/v1/moods/recent?limit=100")
    assert first.status_code == 200
    assert len(first.json()["moods"]) == 1  # now cached under moods:recent:100

    r = await client.post(
        "/api/v1/moods",
        json={**VALID_PAYLOAD, "mood_type": "calm"},
        headers={"user-agent": "ua-2"},
    )
    assert r.status_code == 201

    second = await client.get("/api/v1/moods/recent?limit=100")
    moods = second.json()["moods"]
    assert len(moods) == 2  # stale cache would still say 1
    assert moods[0]["mood_type"] == "calm"


@pytest.mark.asyncio
async def test_map_cache_invalidated_on_submit(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/moods", json=VALID_PAYLOAD, headers={"user-agent": "ua-1"}
    )
    assert r.status_code == 201

    first = await client.get("/api/v1/map?resolution=5")
    assert first.status_code == 200
    total_before = sum(f["properties"]["total"] for f in first.json()["features"])
    assert total_before == 1  # now cached under map:5:{today}

    r = await client.post(
        "/api/v1/moods", json=VALID_PAYLOAD, headers={"user-agent": "ua-2"}
    )
    assert r.status_code == 201

    second = await client.get("/api/v1/map?resolution=5")
    total_after = sum(f["properties"]["total"] for f in second.json()["features"])
    assert total_after == 2  # stale cache would still say 1
