import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    PROJECT_NAME: str = "OmniFlow API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/omniflow"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/omniflow"
    )

    # Supabase
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL", "https://your-supabase-url.supabase.co"
    )
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "your-supabase-anon-key")
    SUPABASE_SERVICE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_KEY", "your-supabase-service-key"
    )

    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")

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
