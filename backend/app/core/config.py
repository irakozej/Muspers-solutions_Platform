from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = Field(
        default="postgresql+psycopg://musper:musper@localhost:5434/musper"
    )

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    # JWT / auth
    jwt_secret: str = "dev-only-change-me-in-production"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    jwt_refresh_remember_ttl_days: int = 30
    reset_token_ttl_minutes: int = 30
    verify_token_ttl_hours: int = 24

    # Cookies
    cookie_domain: str | None = None
    cookie_secure: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
