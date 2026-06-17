import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://xmruser:changeme@localhost:5432/xmrdashboard"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Monero RPC
    monero_rpc_url: str = "http://localhost:18082/json_rpc"

    # Auth
    api_key: str = "changeme"

    # Encryption
    view_key_master_secret: str = "changeme"
    view_key_encryption: bool = True

    # Scanner
    scan_interval: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Security
    cors_origins: str = "http://localhost:3000"
    cookie_secure: bool = True
    cookie_samesite: str = "Strict"

    # Optional
    sentry_dsn: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
