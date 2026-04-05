from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DATABASE_ECHO: bool = False
    MONGO_URL: Optional[str] = None
    MONGO_DB_NAME: str = "org_dev"
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_PREFIX: str = "odk_"
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env"}


settings = Settings()
