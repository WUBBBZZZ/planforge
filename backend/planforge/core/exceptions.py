"""Application exceptions."""

from planforge.domain.enums import TaskStatus


class PlanforgeError(Exception):
    """Base error for domain and service layers."""


class ValidationError(PlanforgeError):
    """Input failed business validation."""


class NotFoundError(PlanforgeError):
    """Entity id does not exist for this owner."""


class StateError(PlanforgeError):
    """Invalid state transition."""


class TaskNotFoundError(NotFoundError):
    """Task id does not exist for this owner."""


class TaskNotEditableError(PlanforgeError):
    """Task cannot be edited in its current state."""


class TaskStateError(StateError):
    """Invalid state transition for a task."""

    def __init__(self, message: str, *, status: TaskStatus) -> None:
        super().__init__(message)
        self.status = status


class BacklogNotFoundError(NotFoundError):
    """Backlog item does not exist."""


class BacklogStateError(StateError):
    """Invalid backlog state transition."""


class RoutineNotFoundError(NotFoundError):
    """Routine does not exist."""


class RoutineStateError(StateError):
    """Invalid routine state transition."""


class OccurrenceNotFoundError(NotFoundError):
    """Occurrence does not exist."""


class OccurrenceStateError(StateError):
    """Invalid occurrence state transition."""


class AppointmentNotFoundError(NotFoundError):
    """Appointment does not exist."""


class AppointmentStateError(StateError):
    """Invalid appointment state transition."""


class AppointmentNotEditableError(PlanforgeError):
    """Appointment cannot be edited in its current state."""


class AppointmentDeleteError(PlanforgeError):
    """Appointment cannot be deleted while audit history exists."""


class MaintenanceNotFoundError(NotFoundError):
    """Maintenance definition does not exist."""


class MaintenanceStateError(StateError):
    """Invalid maintenance state transition."""


class MaintenanceNotEditableError(PlanforgeError):
    """Maintenance cannot be edited in its current state."""


class MaintenanceLinkError(PlanforgeError):
    """Invalid maintenance appointment link."""


class WeeklyTargetNotFoundError(NotFoundError):
    """Weekly target does not exist."""
