"""Hard-coded policy defaults until the settings UI exists."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicySnapshot:
    """Reminder-first policy defaults for view assembly."""

    today_include_rolled_tasks: bool = True
    week_include_overdue_tasks: bool = True
    week_start_day: str = "monday"


def get_policy_snapshot() -> PolicySnapshot:
    """Return the active policy snapshot."""
    return PolicySnapshot()
