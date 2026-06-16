from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CareerGraph AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_profile_model: str | None = None
    openai_direction_model: str | None = None
    openai_advisor_model: str | None = None
    openai_judge_model: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_base_url: str | None = None
    openai_timeout_seconds: float = Field(default=60, gt=0)
    openai_max_retries: int = Field(default=1, ge=0, le=5)
    matching_enable_semantic: bool = True
    matching_enable_llm_judge: bool = False
    career_directions_enable_llm: bool = True
    database_url: str = "postgresql+asyncpg://careergraph:careergraph@localhost:5432/careergraph"
    redis_url: str = "redis://localhost:6379/0"
    allowed_origins: str = "http://localhost:3000"

    @field_validator("openai_base_url", mode="before")
    @classmethod
    def normalize_openai_base_url(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator(
        "openai_profile_model",
        "openai_direction_model",
        "openai_advisor_model",
        "openai_judge_model",
        mode="before",
    )
    @classmethod
    def normalize_optional_model(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
