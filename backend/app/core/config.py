"""Application settings, loaded from environment variables / ``.env``.

Nothing sensitive is hard-coded — every value comes from the environment and
can be overridden. Field names map to upper-case env vars, e.g. ``app_name``
is read from ``APP_NAME``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "crop-care-backend"
    app_version: str = "0.3.0"
    environment: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- CORS (comma-separated; parsed by `cors_origin_list`) ---
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Image uploads ---
    upload_dir: Path = Path("storage/uploads")
    max_upload_size_mb: int = Field(default=10, gt=0)

    # --- Database (PostgreSQL) ---
    # Example: postgresql+psycopg://user:password@localhost:5432/crop_care
    # Deliberately NOT marked required here — `create_db_engine()` raises a
    # clear, actionable error if it is missing when the app starts. This lets
    # Alembic and the tests build `Settings` objects without a live database.
    database_url: str = ""
    db_echo: bool = False

    # --- Machine-learning inference configuration ---
    # Leave both paths empty to keep inference disabled.
    model_artifact_path: str = ""
    model_manifest_path: str = ""
    model_device: str = "cpu"
    model_warmup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        """`cors_origins` parsed into a list, ready for CORSMiddleware."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings object (cached)."""
    return Settings()
