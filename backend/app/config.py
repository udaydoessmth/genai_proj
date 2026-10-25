from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    frontend_origin: str = "http://localhost:5173"


def is_configured(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(normalized) and not normalized.startswith(("your_", "your-"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
