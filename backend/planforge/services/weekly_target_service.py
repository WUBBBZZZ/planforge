"""Weekly target business logic."""

from datetime import UTC, datetime, time

from planforge.core.exceptions import ValidationError, WeeklyTargetNotFoundError
from planforge.domain.enums import CompletionAction, WeeklyTargetStatus
from planforge.domain.local_date import LocalDate
from planforge.models.completion_record import CompletionRecord
from planforge.models.weekly_target import WeeklyTarget
from planforge.services.week_bounds import week_bounds
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _get_target_or_raise(
    session: Session,
    *,
    target_id: str,
    owner_id: str,
) -> WeeklyTarget:
    target = session.scalar(
        select(WeeklyTarget).where(
            WeeklyTarget.id == target_id,
            WeeklyTarget.owner_id == owner_id,
        )
    )
    if target is None:
        raise WeeklyTargetNotFoundError(f"Weekly target not found: {target_id}")
    return target


def create_weekly_target(
    session: Session,
    *,
    owner_id: str,
    title: str,
    target_count: int = 1,
) -> WeeklyTarget:
    """Create an active weekly target."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")
    if target_count < 1:
        raise ValidationError("Target count must be at least 1")

    target = WeeklyTarget(
        owner_id=owner_id,
        title=cleaned_title,
        target_count=target_count,
        status=WeeklyTargetStatus.ACTIVE.value,
    )
    session.add(target)
    session.flush()
    return target


def list_weekly_targets(
    session: Session,
    *,
    owner_id: str,
) -> list[WeeklyTarget]:
    """List active weekly targets."""
    return list(
        session.scalars(
            select(WeeklyTarget)
            .where(
                WeeklyTarget.owner_id == owner_id,
                WeeklyTarget.status == WeeklyTargetStatus.ACTIVE.value,
            )
            .order_by(WeeklyTarget.title)
        )
    )


def update_weekly_target(
    session: Session,
    *,
    target_id: str,
    owner_id: str,
    title: str | None = None,
    target_count: int | None = None,
) -> WeeklyTarget:
    """Update an active weekly target."""
    target = _get_target_or_raise(session, target_id=target_id, owner_id=owner_id)
    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValidationError("Title must not be empty")
        target.title = cleaned_title
    if target_count is not None:
        if target_count < 1:
            raise ValidationError("Target count must be at least 1")
        target.target_count = target_count
    session.flush()
    return target


def delete_weekly_target(
    session: Session,
    *,
    target_id: str,
    owner_id: str,
) -> None:
    """Remove a weekly target."""
    target = _get_target_or_raise(session, target_id=target_id, owner_id=owner_id)
    session.delete(target)
    session.flush()


def log_target_progress(
    session: Session,
    *,
    target_id: str,
    owner_id: str,
) -> WeeklyTarget:
    """Record one unit of progress toward a weekly target."""
    target = _get_target_or_raise(session, target_id=target_id, owner_id=owner_id)
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="weekly_target",
            entity_id=target.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=datetime.now(UTC),
        )
    )
    session.flush()
    return target


def target_progress_for_week(
    session: Session,
    *,
    owner_id: str,
    target: WeeklyTarget,
    week_start: LocalDate,
    week_start_day: str,
) -> tuple[int, int]:
    """Return completed count and target count for the given week."""
    _, week_end = week_bounds(
        reference_date=week_start,
        week_start_day=week_start_day,
    )
    start_dt = datetime.combine(week_start.to_date(), time.min, UTC)
    end_dt = datetime.combine(week_end.add_days(1).to_date(), time.min, UTC)
    completed = session.scalar(
        select(func.count())
        .select_from(CompletionRecord)
        .where(
            CompletionRecord.owner_id == owner_id,
            CompletionRecord.entity_type == "weekly_target",
            CompletionRecord.entity_id == target.id,
            CompletionRecord.action == CompletionAction.COMPLETED.value,
            CompletionRecord.recorded_at >= start_dt,
            CompletionRecord.recorded_at < end_dt,
        )
    )
    return int(completed or 0), target.target_count
