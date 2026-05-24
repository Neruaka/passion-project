"""Application configuration via Pydantic Settings.

All secrets and environment-specific values are read from environment variables
(see .env.example). Never hardcode secrets here. See NFR-SEC-002.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # --- Database ---
    database_url: str

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379/0")

    # --- Auth ---
    jwt_secret: str
    admin_password_hash: str
    system_password_hash: str
    jwt_expiry_days: int = Field(default=7)

    # --- LLM providers ---
    anthropic_api_key: str
    gemini_api_key: str | None = None

    # --- Integrations ---
    hevy_api_key: str | None = None
    cronometer_username: str | None = None
    cronometer_password: str | None = None
    resend_api_key: str | None = None
    ntfy_topic: str | None = None
    recipient_email: str | None = None

    # --- Ingestion (Tasker) ---
    health_ingest_token: str

    # --- Budget ---
    daily_cost_budget_eur: float = Field(default=1.50)
    daily_call_budget: int = Field(default=50)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()  # type: ignore[call-arg]
