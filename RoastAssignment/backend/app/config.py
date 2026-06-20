"""Application settings loaded from environment variables / .env file."""
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Assignment Evaluator backend."""

    APP_NAME: str = "Assignment Evaluator"

    # Database
    DATABASE_URL: str

    # JWT auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth (feature logs-and-skips if empty)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: Optional[List[str]] = None

    # Google Forms/Sheets sync (feature logs-and-skips if empty)
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_FORMS_SHEET_ID: str = ""
    GOOGLE_FORMS_SYNC_INTERVAL_MINUTES: int = 5

    # GitHub API (feature logs-and-skips if empty)
    GITHUB_TOKEN: str = ""
    GITHUB_MAX_FILES: int = 200
    GITHUB_MAX_TOTAL_BYTES: int = 2_000_000
    GITHUB_FETCH_TIMEOUT_SECONDS: int = 30

    # AI roast / evaluation (feature logs-and-skips if empty)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # Email notifications (feature logs-and-skips if empty)
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "noreply@example.com"

    # Evaluation score weighting (must sum to 1.0)
    EVALUATION_AI_WEIGHT: float = 0.6
    EVALUATION_STATIC_WEIGHT: float = 0.4

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def set_allowed_origins(self) -> "Settings":
        """Default ALLOWED_ORIGINS to [FRONTEND_URL] so it tracks env overrides."""
        if self.ALLOWED_ORIGINS is None:
            self.ALLOWED_ORIGINS = [self.FRONTEND_URL]
        return self


settings = Settings()
