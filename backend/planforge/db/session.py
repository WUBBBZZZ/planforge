"""SQLAlchemy engine and session factory."""

from collections.abc import Generator
from pathlib import Path
from urllib.parse import unquote

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create parent directories for file-backed SQLite database URLs."""
    if not database_url.startswith("sqlite"):
        return
    if ":memory:" in database_url:
        return

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return

    db_path = unquote(database_url.removeprefix(prefix))
    if not db_path:
        return

    parent = Path(db_path).expanduser().parent
    if parent != Path("."):
        parent.mkdir(parents=True, exist_ok=True)


def create_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the given database URL."""
    _ensure_sqlite_parent_dir(database_url)

    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = sa_create_engine(database_url, connect_args=connect_args)

    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(
            dbapi_connection: object,
            _connection_record: object,
        ) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


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
