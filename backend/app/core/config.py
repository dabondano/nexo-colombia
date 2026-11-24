"""Application settings, read from environment variables (prefix NEXO_)."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXO_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://nexo:nexo@localhost:5432/nexo"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Owner account, for migrations and grants only (app.core.grants). When unset,
    # everything uses database_url, as in local development.
    migration_database_url: str | None = None
    # The restricted account the application connects as in production.
    app_db_role: str = "nexo_app"

    @field_validator("database_url", "migration_database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str | None) -> str | None:
        """Accept the plain URLs hosting services give (postgres://, postgresql://)."""
        if url is None:
            return None
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url

    @property
    def owner_database_url(self) -> str:
        """The URL migrations and grants run with."""
        return self.migration_database_url or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
