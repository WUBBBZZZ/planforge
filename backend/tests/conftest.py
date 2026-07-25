"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from planforge.core.config import get_settings
from planforge.db.base import Base
from planforge.db.session import create_engine, create_session_factory
from sqlalchemy.orm import Session


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an in-memory database session with schema created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def test_app(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Return a FastAPI app backed by a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("PLANFORGE_DATABASE_URL", database_url)
    get_settings.cache_clear()

    from planforge.main import create_app

    app = create_app()
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    return app
