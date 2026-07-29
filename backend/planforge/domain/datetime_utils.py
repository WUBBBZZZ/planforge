"""UTC datetime normalization helpers."""

from datetime import UTC, datetime


def as_utc_aware(value: datetime) -> datetime:
    """Return a UTC-aware datetime.

    SQLite stores timezone-aware columns as naive UTC strings. Treat naive values
    as UTC rather than the host OS local timezone.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
