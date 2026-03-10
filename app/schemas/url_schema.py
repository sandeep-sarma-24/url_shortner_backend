from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class URLCreate(BaseModel):
    original_url: str
    custom_slug: Optional[str] = None
    title: Optional[str] = None


class URLUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    custom_slug: Optional[str]
    title: Optional[str]
    short_url: str
    is_active: bool
    total_clicks: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class URLListResponse(BaseModel):
    items: list[URLResponse]
    total: int
    page: int
    per_page: int


class ShortenResponse(BaseModel):
    id: int
    original_url: str
    short_url: str
    short_code: str
    created_at: datetime
