from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    extractor: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"

    database_url: str = "sqlite:///./receipts.db"
    upload_dir: str = "uploads"
    max_upload_mb: int = 8
    seed_sample_data: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
