"""Domain enums."""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CompletionAction(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
