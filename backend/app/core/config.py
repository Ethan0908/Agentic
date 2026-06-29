from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://agentic:agentic_password_change_me@localhost:5432/agentic"

    google_places_api_key: str | None = None

    github_token: str | None = None
    github_owner: str = "Ethan0908"
    github_template_repo: str = "business-site-template"
    generated_repo_prefix: str = "lead-"

    vercel_token: str | None = None
    vercel_team_id: str | None = None
    vercel_project_prefix: str = "lead-"

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None
    gmail_sender_email: str | None = None

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
