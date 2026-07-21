"""Environment-based application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load configuration from environment variables and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PLANFORGE_",
        extra="ignore",
    )

    env: str = Field(default="development")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    database_url: str = Field(default="sqlite:///./data/planforge.db")
    secret_key: str = Field(default="replace-with-a-generated-secret")
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
