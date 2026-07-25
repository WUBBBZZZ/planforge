"""Application exceptions."""

from planforge.domain.enums import TaskStatus


class PlanforgeError(Exception):
    """Base error for domain and service layers."""


class ValidationError(PlanforgeError):
    """Input failed business validation."""


class TaskNotFoundError(PlanforgeError):
    """Task id does not exist for this owner."""


class TaskNotEditableError(PlanforgeError):
    """Task cannot be edited in its current state."""


class TaskStateError(PlanforgeError):
    """Invalid state transition for a task."""

    def __init__(self, message: str, *, status: TaskStatus) -> None:
        super().__init__(message)
        self.status = status
