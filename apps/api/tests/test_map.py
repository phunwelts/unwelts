import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_map_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/map")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert data["features"] == []


@pytest.mark.asyncio
async def test_get_map_resolution_7(client: AsyncClient) -> None:
    response = await client.get("/api/v1/map?resolution=7")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"


@pytest.mark.asyncio
async def test_get_map_invalid_resolution(client: AsyncClient) -> None:
    response = await client.get("/api/v1/map?resolution=3")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_map_valid_date(client: AsyncClient) -> None:
    response = await client.get("/api/v1/map?date=2026-03-10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_map_invalid_date(client: AsyncClient) -> None:
    response = await client.get("/api/v1/map?date=not-a-date")
    assert response.status_code == 422
