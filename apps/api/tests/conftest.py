import subprocess
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.db import get_db
from app.db.redis_client import get_redis
from main import app


@pytest.fixture(scope="session", autouse=True)
def run_migrations() -> None:
    """Run alembic migrations once before the entire test suite.

    Runs in a subprocess so it gets its own event loop — avoids conflicts
    with pytest-asyncio's per-test event loop.
    """
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@pytest.fixture()
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Fresh engine per test. Truncates tables on teardown."""
    engine = create_async_engine(settings.database_url)
    yield engine
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE moods, h3_aggregates"))
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture()
async def redis() -> AsyncGenerator[Redis, None]:
    """Fresh Redis client per test. Flushes db on teardown."""
    r: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
    yield r
    await r.flushdb()
    await r.aclose()


@pytest.fixture()
async def client(
    db_engine: AsyncEngine,
    redis: Redis,
) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the test DB and Redis via dependency overrides.

    Mirrors production get_db: a fresh session per request. Reusing one
    session across requests leaks the implicit transaction a GET starts,
    breaking any later request that calls session.begin().
    """
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    async def override_get_redis() -> AsyncGenerator[Redis, None]:
        yield redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
