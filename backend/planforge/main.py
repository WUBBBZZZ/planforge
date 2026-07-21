"""Application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from planforge.api.health import router as health_router
from planforge.core.config import Settings, get_settings
from planforge.core.logging import configure_logging
from planforge.db.session import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown resources."""
    settings = get_settings()
    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    yield

    engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    if settings is not None:
        get_settings.cache_clear()

    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    app = FastAPI(
        title="Planforge",
        version="0.1.0",
        description="Self-hosted personal planning platform API",
        lifespan=lifespan,
    )
    app.include_router(health_router, prefix="/api")

    return app


app = create_app()
