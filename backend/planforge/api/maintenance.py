"""Maintenance API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import MaintenanceStatus
from planforge.domain.local_date import LocalDate
from planforge.models.maintenance import MaintenanceDefinition
from planforge.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


class MaintenanceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    interval_days: int = Field(default=90, ge=1)
    next_due_date: date | None = None


class MaintenanceResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    interval_days: int
    next_due_date: date | None
    status: MaintenanceStatus

    @classmethod
    def from_item(cls, item: MaintenanceDefinition) -> MaintenanceResponse:
        return cls(
            id=item.id,
            title=item.title,
            notes=item.notes,
            interval_days=item.interval_days,
            next_due_date=item.next_due_date,
            status=item.maintenance_status,
        )


@router.get("", response_model=list[MaintenanceResponse])
def list_maintenance_endpoint(
    session: Session = Depends(get_db),
) -> list[MaintenanceResponse]:
    items = maintenance_service.list_maintenance(session, owner_id=LOCAL_OWNER_ID)
    return [MaintenanceResponse.from_item(item) for item in items]


@router.post(
    "", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED
)
def create_maintenance_endpoint(
    body: MaintenanceCreateRequest,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.create_maintenance(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
        interval_days=body.interval_days,
        next_due_date=(
            LocalDate.from_date(body.next_due_date) if body.next_due_date else None
        ),
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/complete", response_model=MaintenanceResponse)
def complete_maintenance_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.complete_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)


@router.post("/{maintenance_id}/pause", response_model=MaintenanceResponse)
def pause_maintenance_endpoint(
    maintenance_id: str,
    session: Session = Depends(get_db),
) -> MaintenanceResponse:
    item = maintenance_service.pause_maintenance(
        session,
        maintenance_id=maintenance_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MaintenanceResponse.from_item(item)
