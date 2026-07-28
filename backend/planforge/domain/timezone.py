"""Timezone helpers with Windows-safe IANA resolution."""

from datetime import UTC, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_timezone(name: str) -> tzinfo:
    """Resolve an IANA timezone name, falling back to UTC when unavailable."""
    normalized = name.strip()
    if normalized.upper() in {"UTC", "ETC/UTC", "GMT"}:
        return UTC

    try:
        return ZoneInfo(normalized)
    except ZoneInfoNotFoundError:
        return UTC
