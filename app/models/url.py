from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.base import TimestampMixin


class URL(Base, TimestampMixin):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), unique=True, index=True, nullable=False)
    custom_slug = Column(String(50), unique=True, nullable=True)
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    clicks = relationship("Click", back_populates="url", cascade="all, delete-orphan")
    user = relationship("User", back_populates="urls")

    @property
    def total_clicks(self) -> int:
        return len(self.clicks) if self.clicks else 0

    @property
    def slug(self) -> str:
        return self.custom_slug or self.short_code
