FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app

# Install system dependencies required by asyncpg and h3
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Keep the venv outside /app so the docker-compose bind mount (./apps/api:/app)
# can't shadow it with a host macOS .venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
