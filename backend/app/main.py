from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.logging import get_logger, setup_logging
from app.settings import ensure_locale_default, ensure_settings_file

logger = get_logger("app")


def create_app() -> FastAPI:
    """Application factory."""
    setup_logging(settings.log_level, settings.log_format)
    logger.info(
        "starting_application",
        log_level=settings.log_level,
        environment=settings.environment,
    )

    # Initialize Sentry in staging/production
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)

    app = FastAPI(
        title="XMR Fund Transparency Suite",
        description="Self-hosted Monero donation transparency tracker — view-key only",
        version="1.1.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
    )

    # CORS
    origins = settings.effective_cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Routers
    from app.api.v1.endpoints import (
        events,
        exports,
        funds,
        health,
        posts,
        reports,
        transactions,
        wallets,
        widget,
    )
    from app.api.v1.endpoints import settings as settings_mod

    app.include_router(wallets.router, prefix="/api/v1")
    app.include_router(funds.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(posts.router, prefix="/api/v1")
    app.include_router(settings_mod.router, prefix="/api/v1")
    app.include_router(widget.router)
    app.include_router(health.router)

    @app.on_event("startup")
    async def startup() -> None:
        ensure_settings_file()
        ensure_locale_default()
        logger.info("application_started")

    @app.on_event("shutdown")
    async def shutdown() -> None:
        logger.info("application_stopped")

    return app


app = create_app()
