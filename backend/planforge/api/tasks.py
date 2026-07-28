"""Task CRUD and lifecycle endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from planforge.api.deps import get_db
from planforge.core.owner import LOCAL_OWNER_ID
from planforge.domain.enums import TaskStatus
from planforge.domain.local_date import LocalDate
from planforge.schemas.backlog import BacklogItemResponse
from planforge.schemas.task import (
    MoveTaskToBacklogResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from planforge.services import task_service
from planforge.services.task_service import UNSET

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
def list_tasks_endpoint(
    session: Session = Depends(get_db),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
) -> list[TaskResponse]:
    """List tasks for the local owner."""
    tasks = task_service.list_tasks(
        session,
        owner_id=LOCAL_OWNER_ID,
        status=status_filter,
    )
    return [TaskResponse.from_task(task) for task in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    body: TaskCreateRequest,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Create a pending task."""
    due_date = LocalDate.from_date(body.due_date) if body.due_date else None
    task = task_service.create_task(
        session,
        owner_id=LOCAL_OWNER_ID,
        title=body.title,
        notes=body.notes,
        due_date=due_date,
    )
    return TaskResponse.from_task(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_endpoint(
    task_id: str,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Return a single task by id."""
    task = task_service.get_task(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return TaskResponse.from_task(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_endpoint(
    task_id: str,
    body: TaskUpdateRequest,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Update a pending task."""
    task = task_service.update_task(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
        title=body.title if "title" in body.model_fields_set else UNSET,
        notes=body.notes if "notes" in body.model_fields_set else UNSET,
        due_date=(
            LocalDate.from_date(body.due_date) if body.due_date is not None else None
        )
        if "due_date" in body.model_fields_set
        else UNSET,
    )
    return TaskResponse.from_task(task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task_endpoint(
    task_id: str,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Mark a task completed."""
    task = task_service.complete_task(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return TaskResponse.from_task(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task_endpoint(
    task_id: str,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Mark a task cancelled."""
    task = task_service.cancel_task(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return TaskResponse.from_task(task)


@router.post("/{task_id}/reopen", response_model=TaskResponse)
def reopen_task_endpoint(
    task_id: str,
    session: Session = Depends(get_db),
) -> TaskResponse:
    """Restore a completed or cancelled task to pending."""
    task = task_service.reopen_task(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return TaskResponse.from_task(task)


@router.post("/{task_id}/move-to-backlog", response_model=MoveTaskToBacklogResponse)
def move_task_to_backlog_endpoint(
    task_id: str,
    session: Session = Depends(get_db),
) -> MoveTaskToBacklogResponse:
    """Move a pending task into the backlog."""
    task, backlog_item = task_service.move_task_to_backlog(
        session,
        task_id=task_id,
        owner_id=LOCAL_OWNER_ID,
    )
    return MoveTaskToBacklogResponse(
        task=TaskResponse.from_task(task),
        backlog_item=BacklogItemResponse.from_item(backlog_item),
    )
