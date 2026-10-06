"""Minimal server settings for Step 1."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings used by the ARYSTOS Core server."""

    model_config = SettingsConfigDict(env_file=".env")

    ADMIN_TOKEN: str = "dev-token-replace-me-with-64-hex-chars-later-please-okay-thanks"
    DATABASE_URL: str = "sqlite:///./arystos.db"
    RELEASES_DIR: str = "releases"
    ENV: str = "dev"


def load_settings() -> Settings:
    """Load and return server settings."""
    return Settings()


ADMIN_TOKEN = load_settings().ADMIN_TOKEN
RELEASES_DIR = Path(load_settings().RELEASES_DIR)
