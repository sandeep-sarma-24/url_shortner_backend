from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from app.configs.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)


class Base(DeclarativeBase):
    pass
