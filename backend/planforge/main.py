"""Application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import planforge.models  # noqa: F401 — register ORM models with metadata
from planforge.api.appointments import router as appointments_router
from planforge.api.backlog import router as backlog_router
from planforge.api.exception_handlers import register_exception_handlers
from planforge.api.health import router as health_router
from planforge.api.maintenance import router as maintenance_router
from planforge.api.routine_groups import router as routine_groups_router
from planforge.api.routines import router as routines_router
from planforge.api.settings import router as settings_router
from planforge.api.tasks import router as tasks_router
from planforge.api.views import router as views_router
from planforge.api.weekly_targets import router as weekly_targets_router
from planforge.core.config import Settings, get_settings
from planforge.core.logging import configure_logging
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.db.migrations import upgrade_database
from planforge.db.session import create_engine, create_session_factory
from planforge.domain.planner_clock import PlannerClock
from planforge.services import routine_group_service, routine_service
from planforge.services.settings_service import (
    ensure_default_settings,
    get_policy_snapshot,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown resources."""
    settings = get_settings()
    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url)
    upgrade_database()
    app.state.engine = engine
    session_factory = create_session_factory(engine)
    app.state.session_factory = session_factory

    bootstrap = session_factory()
    try:
        ensure_default_settings(
            bootstrap,
            owner_id=LOCAL_OWNER_ID,
            bootstrap_timezone=settings.timezone,
        )
        routine_group_service.ensure_default_groups(
            bootstrap,
            owner_id=LOCAL_OWNER_ID,
        )
        policies = get_policy_snapshot(bootstrap, owner_id=LOCAL_OWNER_ID)
        clock = PlannerClock(policies.timezone)
        routine_service.ensure_occurrences(
            bootstrap,
            owner_id=LOCAL_OWNER_ID,
            clock_today=clock.today(),
            policies=policies,
        )
        bootstrap.commit()
    finally:
        bootstrap.close()

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
    register_exception_handlers(app)
    app.include_router(health_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(backlog_router, prefix="/api")
    app.include_router(routines_router, prefix="/api")
    app.include_router(routine_groups_router, prefix="/api")
    app.include_router(appointments_router, prefix="/api")
    app.include_router(maintenance_router, prefix="/api")
    app.include_router(weekly_targets_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(views_router, prefix="/api")

    return app


app = create_app()
