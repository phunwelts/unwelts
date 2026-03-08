import json
import os
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str
    debug: bool = False

    database_url: str
    redis_url: str
    fingerprint_secret: str

    mood_submission_daily_limit: int = 1
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
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
