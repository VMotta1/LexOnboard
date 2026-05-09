from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: str
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "documents"
    ENVIRONMENT: str = "development"
    DEMO_MODE: bool = False
    LEXONBOARD_INLINE_PROCESSING: bool = True

    class Config:
        env_file = ".env"


settings = Settings()