"""Tests for settings validation."""

import pytest
from planforge.services.settings_service import validate_setting, validate_timezone


def test_validate_timezone_accepts_iana_name() -> None:
    validate_timezone("America/New_York")


def test_validate_timezone_rejects_unknown_zone() -> None:
    with pytest.raises(ValueError, match="Invalid timezone"):
        validate_timezone("Not/A_Real_Zone")


def test_validate_setting_timezone() -> None:
    validate_setting("timezone", "Europe/London")
