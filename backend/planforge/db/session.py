"""SQLAlchemy engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the given database URL."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return sa_create_engine(database_url, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a configured session factory bound to the engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session(
    session_factory: sessionmaker[Session],
) -> Generator[Session]:
    """Yield a database session and close it afterward."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
