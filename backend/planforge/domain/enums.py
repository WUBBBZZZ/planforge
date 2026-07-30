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
    ARCHIVED = "archived"
    RESTORED = "restored"


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
    ARCHIVED = "archived"


class AppointmentListFilter(StrEnum):
    UPCOMING = "upcoming"
    TODAY = "today"
    PAST = "past"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"


class MaintenanceStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MaintenanceIntervalUnit(StrEnum):
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"
    MANUAL = "manual"


class MaintenanceNextActionStatus(StrEnum):
    SCHEDULED = "scheduled"
    NEEDS_SCHEDULING = "needs_scheduling"
    REMINDER_SET = "reminder_set"
    NO_NEXT_DATE = "no_next_date"
    NOT_APPLICABLE = "not_applicable"


class MaintenanceListFilter(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"
    NEEDS_SCHEDULING = "needs_scheduling"
    SCHEDULED_UPCOMING = "scheduled_upcoming"
    ACTIVE = "active"
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
    BACKLOG = "backlog"


class PackingEntryType(StrEnum):
    ITEM = "item"
    QUESTION = "question"


class PackingQuestionAnswer(StrEnum):
    YES = "yes"
    NO = "no"
