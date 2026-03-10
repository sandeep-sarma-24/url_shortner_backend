from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClickRecord(BaseModel):
    id: int
    clicked_at: datetime
    ip_address: Optional[str]
    referrer: Optional[str]
    country: Optional[str]
    city: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]

    model_config = {"from_attributes": True}


class TimeSeriesPoint(BaseModel):
    name: str
    clicks: int


class SourceBreakdown(BaseModel):
    name: str
    value: int


class AnalyticsSummary(BaseModel):
    total_clicks: int
    unique_visitors: int
    top_source: str
    top_country: str


class LinkAnalytics(BaseModel):
    link_id: int
    original_url: str
    short_url: str
    short_code: str
    summary: AnalyticsSummary
    clicks_over_time: list[TimeSeriesPoint]
    sources: list[SourceBreakdown]
    countries: list[SourceBreakdown]


class DashboardStats(BaseModel):
    total_clicks: int
    active_links: int
    unique_visitors: int
    clicks_over_time: list[TimeSeriesPoint]
    top_links: list[dict]
