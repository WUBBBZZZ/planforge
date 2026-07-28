"""Maintenance business logic."""

from datetime import UTC, datetime, timedelta

from planforge.core.exceptions import (
    MaintenanceNotFoundError,
    MaintenanceStateError,
    ValidationError,
)
from planforge.domain.enums import CompletionAction, MaintenanceStatus
from planforge.domain.local_date import LocalDate
from planforge.models.completion_record import CompletionRecord
from planforge.models.maintenance import MaintenanceDefinition
from sqlalchemy import select
from sqlalchemy.orm import Session


def _get_maintenance_or_raise(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    item = session.scalar(
        select(MaintenanceDefinition).where(
            MaintenanceDefinition.id == maintenance_id,
            MaintenanceDefinition.owner_id == owner_id,
        )
    )
    if item is None:
        raise MaintenanceNotFoundError(f"Maintenance item not found: {maintenance_id}")
    return item


def create_maintenance(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
    interval_days: int = 90,
    next_due_date: LocalDate | None = None,
) -> MaintenanceDefinition:
    """Create an active maintenance definition."""
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValidationError("Title must not be empty")
    if interval_days < 1:
        raise ValidationError("Interval must be at least 1 day")

    due = next_due_date or LocalDate.from_date(datetime.now(UTC).date())
    item = MaintenanceDefinition(
        owner_id=owner_id,
        title=cleaned_title,
        notes=notes,
        interval_days=interval_days,
        next_due_date=due.to_date(),
        status=MaintenanceStatus.ACTIVE.value,
    )
    session.add(item)
    session.flush()
    return item


def list_maintenance(
    session: Session,
    *,
    owner_id: str,
    status: MaintenanceStatus | None = MaintenanceStatus.ACTIVE,
) -> list[MaintenanceDefinition]:
    """List maintenance definitions."""
    query = select(MaintenanceDefinition).where(
        MaintenanceDefinition.owner_id == owner_id
    )
    if status is not None:
        query = query.where(MaintenanceDefinition.status == status.value)
    query = query.order_by(MaintenanceDefinition.title)
    return list(session.scalars(query))


def complete_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
    completed_on: LocalDate | None = None,
) -> MaintenanceDefinition:
    """Complete maintenance and schedule the next due date."""
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance items can be completed")

    now = datetime.now(UTC)
    item.last_completed_at = now
    base_date = completed_on.to_date() if completed_on is not None else now.date()
    item.next_due_date = base_date + timedelta(days=item.interval_days)
    session.add(
        CompletionRecord(
            owner_id=owner_id,
            entity_type="maintenance",
            entity_id=item.id,
            action=CompletionAction.COMPLETED.value,
            recorded_at=now,
        )
    )
    session.flush()
    return item


def pause_maintenance(
    session: Session,
    *,
    maintenance_id: str,
    owner_id: str,
) -> MaintenanceDefinition:
    """Pause maintenance reminders."""
    item = _get_maintenance_or_raise(
        session,
        maintenance_id=maintenance_id,
        owner_id=owner_id,
    )
    if item.maintenance_status is not MaintenanceStatus.ACTIVE:
        raise MaintenanceStateError("Only active maintenance items can be paused")
    item.status = MaintenanceStatus.PAUSED.value
    session.flush()
    return item
