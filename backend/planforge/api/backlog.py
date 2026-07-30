"""Backlog API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.local_date import LocalDate
from planforge.schemas.backlog import BacklogItemResponse
from planforge.schemas.task import TaskResponse
from planforge.services import backlog_service

router = APIRouter(prefix="/backlog", tags=["backlog"])


class BacklogCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None


class PromoteBacklogRequest(BaseModel):
    due_date: date


class PromoteBacklogResponse(BaseModel):
    backlog: BacklogItemResponse
    task: TaskResponse


@router.get("", response_model=list[BacklogItemResponse])
def list_backlog_endpoint(
    session: Session = Depends(get_db),
) -> list[BacklogItemResponse]:
    items = backlog_service.list_backlog_items(session, owner_id=LOCAL_OWNER_ID)
    return [BacklogItemResponse.from_item(item) for item in items]


@router.post(
    "",
    response_model=BacklogItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_backlog_endpoint(
    body: BacklogCreateRequest,
    session: Session = Depends(get_db),
) -> BacklogItemResponse:
    item = backlog_service.create_backlog_item(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
    )
    return BacklogItemResponse.from_item(item)


@router.post("/{item_id}/archive", response_model=BacklogItemResponse)
def archive_backlog_endpoint(
    item_id: str,
    session: Session = Depends(get_db),
) -> BacklogItemResponse:
    item = backlog_service.archive_backlog_item(
        session,
        item_id=item_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return BacklogItemResponse.from_item(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backlog_endpoint(
    item_id: str,
    session: Session = Depends(get_db),
) -> None:
    backlog_service.delete_backlog_item(
        session,
        item_id=item_id,
        owner_id=LOCAL_OWNER_ID,
    )


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
        backlog=BacklogItemResponse.from_item(item),
        task=TaskResponse.from_task(task),
    )
