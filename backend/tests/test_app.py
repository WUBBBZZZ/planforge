"""Tests for application construction and configuration."""

import pytest
from planforge.core.config import Settings, get_settings
from planforge.main import create_app


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app()
    assert app.title == "Planforge"


def test_default_settings_use_loopback_host() -> None:
    get_settings.cache_clear()
    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000


def test_settings_override_from_fabricated_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("PLANFORGE_HOST", "127.0.0.1")
    monkeypatch.setenv("PLANFORGE_PORT", "9001")
    monkeypatch.setenv("PLANFORGE_DATABASE_URL", "sqlite:///./data/example-test.db")
    monkeypatch.setenv("PLANFORGE_SECRET_KEY", "fabricated-test-secret-not-real")

    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 9001
    assert settings.database_url == "sqlite:///./data/example-test.db"
    assert settings.secret_key == "fabricated-test-secret-not-real"
