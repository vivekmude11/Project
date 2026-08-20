"""Application configuration — all secrets come from environment variables.
Never hardcode API keys (spec section 16)."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Stock Intelligence AI"
    environment: str = "development"
    debug: bool = False

    # --- Security ---
    jwt_secret: str = "CHANGE_ME"          # override via env in every environment
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60
    refresh_token_ttl_days: int = 30

    # --- Datastores ---
    database_url: str = "postgresql+asyncpg://sia:sia@localhost:5432/sia"
    redis_url: str = "redis://localhost:6379/0"

    # --- Market data providers (set only what you use) ---
    angelone_api_key: str | None = None
    angelone_client_id: str | None = None
    dhan_access_token: str | None = None
    zerodha_api_key: str | None = None
    zerodha_api_secret: str | None = None
    truedata_user: str | None = None
    truedata_password: str | None = None
    globaldatafeeds_api_key: str | None = None

    # --- Global market + news ---
    alphavantage_api_key: str | None = None
    finnhub_api_key: str | None = None
    marketaux_api_key: str | None = None

    # --- LLM (reasoning / RAG / chat) ---
    llm_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-6"
    embedding_model: str = "text-embedding-3-small"  # dim must match rag_documents.embedding

    # --- Push ---
    fcm_server_key: str | None = None

    # --- Rate limiting ---
    rate_limit_per_minute: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
