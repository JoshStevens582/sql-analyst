from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SQL_ANALYST_", env_file=".env", extra="ignore")

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENAI_API_KEY",
            "SQL_ANALYST_OPENAI_API_KEY",
            "openai_api_key",
        ),
    )
    openai_model: str = "gpt-4.1-mini"
    database_path: Path = Path("data/demo.db")
    max_retries: int = 3
    max_rows: int = 200
    recursion_limit: int = 25


def get_settings() -> Settings:
    return Settings()