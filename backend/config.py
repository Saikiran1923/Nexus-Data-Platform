from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Nexus One"
    app_version: str = "3.0.0"
    environment: str = "local"

    database_url: str = "postgresql://nexus:nexus@localhost:5432/nexus"

    jwt_secret_key: str = "change-me-in-production-use-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 50 * 1024 * 1024
    allowed_upload_extensions: List[str] = [".csv"]
    allowed_upload_content_types: List[str] = ["text/csv", "application/csv", "application/vnd.ms-excel"]

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False

    cors_origins: List[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
