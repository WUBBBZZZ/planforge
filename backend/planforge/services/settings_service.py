"""Default settings and policy resolution."""

from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from planforge.core.owner import LOCAL_OWNER_ID
from planforge.models.setting import Setting
from sqlalchemy import select
from sqlalchemy.orm import Session

DEFAULT_SETTINGS: dict[str, str] = {
    "today.include_rolled_tasks": "yes",
    "today.include_routine_occurrences": "all_due",
    "week.show_completed": "yes",
    "week.include_overdue_tasks": "yes",
    "routine.missed_behavior": "prompt",
    "task.overdue_behavior": "roll_to_today",
    "day_boundary.time": "midnight_local",
    "week.start_day": "monday",
    "routine.horizon_days": "medium",
    "maintenance.lead_days": "7",
    "app.default_landing_view": "week",
    "capture.entry_style": "modal",
    "timezone": "UTC",
}

HORIZON_DAYS: dict[str, int] = {
    "short": 14,
    "medium": 30,
    "long": 90,
}

VALID_SETTINGS: dict[str, set[str]] = {
    "today.include_rolled_tasks": {"yes", "no"},
    "today.include_routine_occurrences": {"all_due"},
    "week.show_completed": {"yes", "no"},
    "week.include_overdue_tasks": {"yes", "no"},
    "routine.missed_behavior": {"mark_missed", "roll_forward", "prompt"},
    "task.overdue_behavior": {
        "stay_pending",
        "roll_to_today",
        "hide_until_rescheduled",
    },
    "day_boundary.time": {"midnight_local"},
    "week.start_day": {"monday", "sunday", "saturday"},
    "routine.horizon_days": {"short", "medium", "long"},
    "maintenance.lead_days": {"1", "3", "7", "14", "30"},
    "app.default_landing_view": {"week", "today"},
    "capture.entry_style": {"modal", "page", "inline"},
}


@dataclass(frozen=True)
class PolicySnapshot:
    """Resolved policy values for view assembly."""

    today_include_rolled_tasks: bool = True
    today_include_routine_occurrences: bool = True
    week_show_completed: bool = True
    week_include_overdue_tasks: bool = True
    week_start_day: str = "monday"
    routine_horizon_days: int = 30
    maintenance_lead_days: int = 7
    timezone: str = "UTC"


def ensure_default_settings(
    session: Session, *, owner_id: str = LOCAL_OWNER_ID
) -> None:
    """Insert missing default settings for an owner."""
    existing = {
        row.key
        for row in session.scalars(select(Setting).where(Setting.owner_id == owner_id))
    }
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            session.add(Setting(owner_id=owner_id, key=key, value=value))
    session.flush()


def get_settings_map(
    session: Session,
    *,
    owner_id: str = LOCAL_OWNER_ID,
) -> dict[str, str]:
    """Return all settings for an owner, including defaults."""
    ensure_default_settings(session, owner_id=owner_id)
    values = dict(DEFAULT_SETTINGS)
    rows = session.scalars(select(Setting).where(Setting.owner_id == owner_id))
    for row in rows:
        values[row.key] = row.value
    return values


def get_policy_snapshot(
    session: Session,
    *,
    owner_id: str = LOCAL_OWNER_ID,
) -> PolicySnapshot:
    """Build a policy snapshot from persisted settings."""
    settings = get_settings_map(session, owner_id=owner_id)
    horizon_key = settings["routine.horizon_days"]
    return PolicySnapshot(
        today_include_rolled_tasks=settings["today.include_rolled_tasks"] == "yes",
        today_include_routine_occurrences=(
            settings["today.include_routine_occurrences"] == "all_due"
        ),
        week_show_completed=settings["week.show_completed"] == "yes",
        week_include_overdue_tasks=settings["week.include_overdue_tasks"] == "yes",
        week_start_day=settings["week.start_day"],
        routine_horizon_days=HORIZON_DAYS.get(horizon_key, 30),
        maintenance_lead_days=int(settings["maintenance.lead_days"]),
        timezone=settings["timezone"],
    )


def validate_timezone(value: str) -> None:
    """Raise ValueError when a timezone name is not a valid IANA identifier."""
    normalized = value.strip()
    if not normalized:
        raise ValueError("Timezone must not be empty")
    if normalized.upper() in {"UTC", "ETC/UTC", "GMT"}:
        return
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Invalid timezone: {value}") from exc


def validate_setting(key: str, value: str) -> None:
    """Raise ValueError when a setting key or value is invalid."""
    if key not in DEFAULT_SETTINGS:
        raise ValueError(f"Unknown setting key: {key}")
    if key == "timezone":
        validate_timezone(value)
        return
    if value not in VALID_SETTINGS[key]:
        raise ValueError(f"Invalid value for {key}: {value}")


def update_setting(
    session: Session,
    *,
    owner_id: str,
    key: str,
    value: str,
) -> Setting:
    """Create or update a single setting."""
    validate_setting(key, value)
    ensure_default_settings(session, owner_id=owner_id)
    row = session.scalar(
        select(Setting).where(Setting.owner_id == owner_id, Setting.key == key)
    )
    if row is None:
        row = Setting(owner_id=owner_id, key=key, value=value)
        session.add(row)
    else:
        row.value = value
    session.flush()
    return row
