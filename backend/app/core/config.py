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

    # Transactional email (Resend). If the key is unset in development, reset
    # links fall back to the server log so local dev works without an account.
    resend_api_key: str = ""
    email_from: str = "MusperSolutions <onboarding@resend.dev>"

    # Cookies
    cookie_domain: str | None = None
    cookie_secure: bool = False

    # Anthropic Claude API for the diagnostic chatbot
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    claude_max_tokens: int = 1024
    # Hard timeout on each Claude call so a hanging request can't freeze a worker.
    claude_timeout_seconds: float = 45.0
    # Report generation is a single bigger call: more output room, longer timeout.
    claude_report_max_tokens: int = 3000
    claude_report_timeout_seconds: float = 120.0
    # Cost ceiling: max user turns per interview (~3x a normal 20-turn interview).
    # On reaching the cap the interview closes gracefully and is marked completed.
    diagnostic_max_user_turns: int = 60

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
