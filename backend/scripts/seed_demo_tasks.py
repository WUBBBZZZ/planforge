"""Seed fabricated demo tasks for local development."""

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.db.base import Base
from planforge.db.session import create_engine, create_session_factory
from planforge.domain.local_date import LocalDate
from planforge.services import task_service


def main() -> None:
    """Insert demo tasks into the local database."""
    from planforge.core.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    session = session_factory()

    try:
        today = LocalDate.from_iso("2026-07-21")
        task_service.create_task(
            session,
            owner_id=LOCAL_OWNER_ID,
            title="Water the plants",
            due_date=today,
        )
        task_service.create_task(
            session,
            owner_id=LOCAL_OWNER_ID,
            title="Example overdue errand",
            due_date=today.add_days(-3),
        )
        task_service.create_task(
            session,
            owner_id=LOCAL_OWNER_ID,
            title="Future demo task",
            due_date=today.add_days(7),
        )
        task_service.create_task(
            session,
            owner_id=LOCAL_OWNER_ID,
            title="Unscheduled idea",
            due_date=None,
        )
        session.commit()
        print("Seeded 4 fabricated demo tasks.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
