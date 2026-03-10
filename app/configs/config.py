from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/url_shortener"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    CACHE_TTL_SECONDS: int = 600
    CACHE_LRU_MAX_SIZE: int = 2048

    class Config:
        env_file = ".env.development"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
