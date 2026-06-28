import os
from pathlib import Path
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

# Canonical env source: repository root .env
root_env = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(root_env, override=False)


class Settings(BaseModel):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    PROJECT_NAME: str = "OmniFlow API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database — required, no fallback
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", "")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "DATABASE_URL is not set. Populate omniflow/.env before starting the backend."
            )
        return v

    @field_validator("SYNC_DATABASE_URL")
    @classmethod
    def sync_database_url_must_be_set(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "SYNC_DATABASE_URL is not set. Populate omniflow/.env before starting the backend."
            )
        return v

    # Supabase (optional for local dev)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # OpenRouter AI
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    DEFAULT_WORKSPACE_ID: str = os.getenv("DEFAULT_WORKSPACE_ID", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "omniflow_telegram_secret_token")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 15
    RATE_LIMIT_PER_DAY: int = 100

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Router Settings
    ROUTER_CONFIDENCE_THRESHOLD: float = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.70"))


settings = Settings()
