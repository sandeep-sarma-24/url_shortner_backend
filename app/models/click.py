from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id", ondelete="CASCADE"), nullable=False, index=True)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    referrer = Column(String(2048), nullable=True)
    country = Column(String(100), nullable=True)
    country_code = Column(String(10), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(100), nullable=True)
    isp = Column(String(200), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    url = relationship("URL", back_populates="clicks")
