"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "FAQ & Chat API"
    debug: bool = False
    database_url: str = "sqlite:///./faq_mvp.sqlite"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_transcription_api_key: str | None = None

    openrouter_api_key: str | None = None
    openrouter_site_url: str = "http://127.0.0.1:8000"
    openrouter_app_name: str = "FAQ Chat Application"
    openrouter_model: str = "openai/gpt-4o-mini"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
