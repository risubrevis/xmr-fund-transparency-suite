from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    environment: str = "local"
    app_url: str = "localhost"

    # Database
    database_url: str = (
        "postgresql+asyncpg://xmruser:changeme@localhost:5432/xmrdashboard"
    )

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

    # Security — derived from ENVIRONMENT when not explicitly set
    cors_origins: str = ""
    cookie_secure: str = ""  # "true"/"false"/"" (empty = auto-detect from ENVIRONMENT)
    cookie_samesite: str = "Strict"

    # Optional
    sentry_dsn: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_production(self) -> bool:
        return self.environment in ("production", "staging")

    @property
    def app_origin(self) -> str:
        """Full origin URL derived from APP_URL and ENVIRONMENT."""
        scheme = "https" if self.is_production else "http"
        return f"{scheme}://{self.app_url}"

    @property
    def effective_cors_origins(self) -> list[str]:
        """CORS origins: explicit CORS_ORIGINS + APP_URL, with localhost fallback in local/dev."""
        origins: list[str] = []
        if self.cors_origins:
            origins.extend(o.strip() for o in self.cors_origins.split(",") if o.strip())
        origins.append(self.app_origin)
        if not self.is_production:
            origins.append("http://localhost:3000")
        return list(dict.fromkeys(origins))

    @property
    def effective_cookie_secure(self) -> bool:
        """Secure cookies only over HTTPS (production). Explicit override takes precedence."""
        if self.cookie_secure.lower() == "true":
            return True
        if self.cookie_secure.lower() == "false":
            return False
        return self.is_production


settings = Settings()
