"""Domain enums."""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MOVED_TO_BACKLOG = "moved_to_backlog"


class CompletionAction(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    REOPENED = "reopened"
    MOVED_TO_BACKLOG = "moved_to_backlog"


class BacklogStatus(StrEnum):
    ACTIVE = "active"
    PROMOTED = "promoted"
    ARCHIVED = "archived"


class RoutineStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class OccurrenceStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    MISSED = "missed"


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class WeeklyTargetStatus(StrEnum):
    ACTIVE = "active"
    MET = "met"
    UNMET = "unmet"


class ViewItemKind(StrEnum):
    TASK = "task"
    OCCURRENCE = "occurrence"
    APPOINTMENT = "appointment"
    MAINTENANCE = "maintenance"
