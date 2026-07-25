"""Pydantic schemas for tasks."""

from datetime import date, datetime

from planforge.domain.enums import TaskStatus
from planforge.models.task import Task
from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None
    due_date: date | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    notes: str | None
    due_date: date | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_task(cls, task: Task) -> TaskResponse:
        return cls(
            id=task.id,
            title=task.title,
            notes=task.notes,
            due_date=task.due_date,
            status=TaskStatus(task.status),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
