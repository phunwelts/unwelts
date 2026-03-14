import json
import os
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str
    debug: bool = False

    database_url: str
    redis_url: str
    fingerprint_secret: str

    cors_origins: list[str] = ["http://localhost:3000"]

    db_pool_size: int = 5
    db_max_overflow: int = 5

    # Rolling window for fingerprint-based rate limit.
    # Default 24 h keeps existing prod semantics; reduce in dev/staging as needed.
    rate_limit_window_hours: int = 24

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v

    @field_validator("fingerprint_secret")
    @classmethod
    def validate_fingerprint_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("fingerprint_secret must be at least 32 characters")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str], info: ValidationInfo) -> list[str]:
        app_env = info.data.get("app_env", "development")
        if app_env == "production":
            for origin in v:
                if "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError(
                        "cors_origins contains a localhost entry in production — "
                        "set CORS_ORIGINS to your production domain"
                    )
        return v


def _fetch_from_secrets_manager() -> dict[str, Any]:
    secret_name = os.environ["AWS_SECRET_NAME"]
    region = os.environ["AWS_REGION"]

    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(
            f"Failed to fetch secret '{secret_name}' from Secrets Manager: {e}"
        ) from e

    return cast(dict[str, Any], json.loads(response["SecretString"]))


def build_settings() -> Settings:
    app_env = os.environ.get("APP_ENV", "development")

    if app_env == "production":
        secrets = _fetch_from_secrets_manager()
        return Settings(app_env=app_env, **secrets)

    # Development: all variables are injected by Docker Compose into os.environ
    return Settings(app_env=app_env)  # type: ignore[call-arg]


settings = build_settings()
