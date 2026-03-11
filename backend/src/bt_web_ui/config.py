"""Application configuration using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8080
    db_path: Path = Path("data/bt_web_ui.db")
    adapter: str | None = None
    log_level: str = "INFO"

    model_config = {
        "env_prefix": "BT_WEB_UI_",
    }


def get_settings() -> Settings:
    """Return application settings singleton."""
    return Settings()
