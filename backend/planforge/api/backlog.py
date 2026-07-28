"""Backlog API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import BacklogStatus
from planforge.domain.local_date import LocalDate
from planforge.models.backlog_item import BacklogItem
from planforge.schemas.task import TaskResponse
from planforge.services import backlog_service

router = APIRouter(prefix="/backlog", tags=["backlog"])


class BacklogCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None


class BacklogResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    status: BacklogStatus
    promoted_entity_type: str | None
    promoted_entity_id: str | None

    @classmethod
    def from_item(cls, item: BacklogItem) -> BacklogResponse:
        return cls(
            id=item.id,
            title=item.title,
            notes=item.notes,
            status=item.backlog_status,
            promoted_entity_type=item.promoted_entity_type,
            promoted_entity_id=item.promoted_entity_id,
        )


class PromoteBacklogRequest(BaseModel):
    due_date: date


class PromoteBacklogResponse(BaseModel):
    backlog: BacklogResponse
    task: TaskResponse


@router.get("", response_model=list[BacklogResponse])
def list_backlog_endpoint(session: Session = Depends(get_db)) -> list[BacklogResponse]:
    items = backlog_service.list_backlog_items(session, owner_id=LOCAL_OWNER_ID)
    return [BacklogResponse.from_item(item) for item in items]


@router.post("", response_model=BacklogResponse, status_code=status.HTTP_201_CREATED)
def create_backlog_endpoint(
    body: BacklogCreateRequest,
    session: Session = Depends(get_db),
) -> BacklogResponse:
    item = backlog_service.create_backlog_item(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
    )
    return BacklogResponse.from_item(item)


@router.post("/{item_id}/archive", response_model=BacklogResponse)
def archive_backlog_endpoint(
    item_id: str,
    session: Session = Depends(get_db),
) -> BacklogResponse:
    item = backlog_service.archive_backlog_item(
        session,
        item_id=item_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return BacklogResponse.from_item(item)


@router.post("/{item_id}/promote", response_model=PromoteBacklogResponse)
def promote_backlog_endpoint(
    item_id: str,
    body: PromoteBacklogRequest,
    session: Session = Depends(get_db),
) -> PromoteBacklogResponse:
    item, task = backlog_service.promote_backlog_to_task(
        session,
        item_id=item_id,
        owner_id=LOCAL_OWNER_ID,
        due_date=LocalDate.from_date(body.due_date),
    )
    return PromoteBacklogResponse(
        backlog=BacklogResponse.from_item(item),
        task=TaskResponse.from_task(task),
    )
