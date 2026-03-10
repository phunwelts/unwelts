import pytest
from httpx import AsyncClient

VALID_PAYLOAD = {"lat": 40.7128, "lng": -74.0060, "mood_type": "happy"}


@pytest.mark.asyncio
async def test_submit_mood_success(client: AsyncClient) -> None:
    response = await client.post("/api/v1/moods", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["mood_type"] == "happy"
    assert "id" in data
    assert "submitted_at" in data


@pytest.mark.asyncio
async def test_submit_mood_rate_limit(client: AsyncClient) -> None:
    r1 = await client.post("/api/v1/moods", json=VALID_PAYLOAD)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/moods", json=VALID_PAYLOAD)
    assert r2.status_code == 429
    assert "already submitted" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_submit_mood_invalid_lat(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/moods", json={**VALID_PAYLOAD, "lat": 999}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_mood_invalid_mood_type(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/moods", json={**VALID_PAYLOAD, "mood_type": "furious"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_mood_note_too_long(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/moods", json={**VALID_PAYLOAD, "note": "x" * 501}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_recent_moods_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/moods/recent")
    assert response.status_code == 200
    assert response.json()["moods"] == []


@pytest.mark.asyncio
async def test_recent_moods_returns_submitted(client: AsyncClient) -> None:
    await client.post("/api/v1/moods", json=VALID_PAYLOAD)
    response = await client.get("/api/v1/moods/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data["moods"]) == 1
    mood = data["moods"][0]
    assert mood["mood_type"] == "happy"
    assert "lat" in mood
    assert "lng" in mood
    assert mood["city"] is None


@pytest.mark.asyncio
async def test_recent_moods_limit(client: AsyncClient) -> None:
    # Submit one mood (rate limit prevents more from same client)
    await client.post("/api/v1/moods", json=VALID_PAYLOAD)
    response = await client.get("/api/v1/moods/recent?limit=1")
    assert response.status_code == 200
    assert len(response.json()["moods"]) == 1


@pytest.mark.asyncio
async def test_recent_moods_invalid_limit(client: AsyncClient) -> None:
    response = await client.get("/api/v1/moods/recent?limit=0")
    assert response.status_code == 422
