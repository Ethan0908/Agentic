from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://agentic:agentic_password_change_me@localhost:5432/agentic"

    google_places_api_key: str | None = None

    openai_api_key: str | None = None
    openai_email_model: str = "gpt-5.5"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Denny"
    smtp_use_tls: bool = True
    smtp_reply_to: str | None = None

    github_token: str | None = None
    github_owner: str = "Ethan0908"
    github_template_repo: str = "business-site-template"

    vercel_token: str | None = None
    vercel_team_id: str | None = None

    public_app_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    default_no_response_days: int = 30
    allow_auto_send_emails: bool = False
    allow_auto_delete_deployments: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
