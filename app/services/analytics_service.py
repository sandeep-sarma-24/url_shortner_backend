from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, extract
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

from app.models.url import URL
from app.models.click import Click
from app.core.exceptions import NotFoundException
from app.utils.helpers import get_referrer_source
from app.services.url_service import build_short_url


def _build_geo_points(clicks: list) -> list[dict]:
    country_data: dict[str, dict] = {}
    total_geo_clicks = 0
    for c in clicks:
        if not c.latitude or not c.longitude or not c.country:
            continue
        total_geo_clicks += 1
        cc = c.country_code or c.country
        if cc not in country_data:
            country_data[cc] = {
                "country": c.country,
                "country_code": c.country_code,
                "lat": c.latitude,
                "lng": c.longitude,
                "clicks": 0,
                "cities": set(),
                "regions": set(),
            }
        country_data[cc]["clicks"] += 1
        if c.city:
            country_data[cc]["cities"].add(c.city)
        if c.region:
            country_data[cc]["regions"].add(c.region)

    results = []
    for item in country_data.values():
        results.append({
            "country": item["country"],
            "country_code": item["country_code"],
            "lat": item["lat"],
            "lng": item["lng"],
            "clicks": item["clicks"],
            "cities": sorted(item["cities"])[:5],
            "regions": sorted(item["regions"])[:5],
            "percentage": round((item["clicks"] / total_geo_clicks) * 100, 1) if total_geo_clicks else 0,
        })
    return results


def _build_recent_clicks(clicks: list, limit: int = 20) -> list[dict]:
    sorted_clicks = sorted(clicks, key=lambda c: c.clicked_at or datetime.min, reverse=True)
    results = []
    for c in sorted_clicks[:limit]:
        results.append({
            "id": c.id,
            "ip_address": c.ip_address,
            "country": c.country,
            "country_code": c.country_code,
            "region": c.region,
            "city": c.city,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "timezone": c.timezone,
            "isp": c.isp,
            "device_type": c.device_type,
            "browser": c.browser,
            "os": c.os,
            "referrer": c.referrer,
            "clicked_at": c.clicked_at.isoformat() if c.clicked_at else None,
        })
    return results


def get_link_analytics(db: Session, url_id: int, user_id: int | None = None) -> dict:
    query = db.query(URL).filter(URL.id == url_id)
    if user_id is not None:
        query = query.filter(URL.user_id == user_id)
    url = query.first()
    if not url:
        raise NotFoundException("URL not found")

    clicks = db.query(Click).filter(Click.url_id == url_id).all()

    total_clicks = len(clicks)
    unique_ips = len(set(c.ip_address for c in clicks if c.ip_address))

    source_counter: Counter = Counter()
    country_counter: Counter = Counter()
    device_counter: Counter = Counter()
    browser_counter: Counter = Counter()
    os_counter: Counter = Counter()
    for click in clicks:
        source_counter[get_referrer_source(click.referrer)] += 1
        country_counter[click.country or "Unknown"] += 1
        device_counter[click.device_type or "Unknown"] += 1
        browser_counter[click.browser or "Unknown"] += 1
        os_counter[click.os or "Unknown"] += 1

    top_source = source_counter.most_common(1)[0][0] if source_counter else "Direct"
    top_country = country_counter.most_common(1)[0][0] if country_counter else "Unknown"

    now = datetime.now(timezone.utc)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    clicks_by_day: dict[str, int] = {d: 0 for d in day_names}
    for click in clicks:
        if click.clicked_at and click.clicked_at >= now - timedelta(days=7):
            day_name = day_names[click.clicked_at.weekday()]
            clicks_by_day[day_name] += 1

    clicks_over_time = [{"name": d, "clicks": clicks_by_day[d]} for d in day_names]

    sources = [{"name": name, "value": count} for name, count in source_counter.most_common(5)]
    if not sources:
        sources = [{"name": "Direct", "value": 0}]

    countries = [{"name": name, "value": count} for name, count in country_counter.most_common(5)]
    if not countries:
        countries = [{"name": "Unknown", "value": 0}]

    devices = [{"name": name, "value": count} for name, count in device_counter.most_common(5)]
    browsers = [{"name": name, "value": count} for name, count in browser_counter.most_common(5)]
    operating_systems = [{"name": name, "value": count} for name, count in os_counter.most_common(5)]

    return {
        "link_id": url.id,
        "original_url": url.original_url,
        "short_url": build_short_url(url),
        "short_code": url.slug,
        "summary": {
            "total_clicks": total_clicks,
            "unique_visitors": unique_ips,
            "top_source": top_source,
            "top_country": top_country,
        },
        "clicks_over_time": clicks_over_time,
        "sources": sources,
        "countries": countries,
        "devices": devices,
        "browsers": browsers,
        "operating_systems": operating_systems,
        "geo_points": _build_geo_points(clicks),
        "recent_clicks": _build_recent_clicks(clicks),
    }


def get_dashboard_stats(db: Session, user_id: int) -> dict:
    urls = db.query(URL).filter(URL.user_id == user_id).all()
    url_ids = [u.id for u in urls]

    total_clicks = 0
    unique_ips = set()
    all_clicks = []
    if url_ids:
        total_clicks = db.query(func.count(Click.id)).filter(Click.url_id.in_(url_ids)).scalar() or 0
        unique_ip_rows = (
            db.query(Click.ip_address)
            .filter(Click.url_id.in_(url_ids), Click.ip_address.isnot(None))
            .distinct()
            .all()
        )
        unique_ips = set(r[0] for r in unique_ip_rows)
        all_clicks = (
            db.query(Click)
            .filter(Click.url_id.in_(url_ids))
            .order_by(Click.clicked_at.desc())
            .limit(100)
            .all()
        )

    active_links = sum(1 for u in urls if u.is_active)

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    now = datetime.now(timezone.utc)
    clicks_by_month: dict[str, int] = {}
    for i in range(6, -1, -1):
        dt = now - timedelta(days=30 * i)
        month_name = month_names[dt.month - 1]
        clicks_by_month[month_name] = 0

    if url_ids:
        seven_months_ago = now - timedelta(days=210)
        month_clicks = (
            db.query(
                extract("month", Click.clicked_at).label("month"),
                func.count(Click.id).label("count"),
            )
            .filter(Click.url_id.in_(url_ids), Click.clicked_at >= seven_months_ago)
            .group_by("month")
            .all()
        )
        for row in month_clicks:
            month_idx = int(row.month) - 1
            month_name = month_names[month_idx]
            if month_name in clicks_by_month:
                clicks_by_month[month_name] = row.count

    clicks_over_time = [{"name": m, "clicks": c} for m, c in clicks_by_month.items()]

    top_links = []
    if url_ids:
        link_click_counts = (
            db.query(Click.url_id, func.count(Click.id).label("cnt"))
            .filter(Click.url_id.in_(url_ids))
            .group_by(Click.url_id)
            .order_by(func.count(Click.id).desc())
            .limit(5)
            .all()
        )
        url_map = {u.id: u for u in urls}
        for row in link_click_counts:
            u = url_map.get(row.url_id)
            if u:
                top_links.append({
                    "id": u.slug,
                    "original": u.original_url,
                    "short": build_short_url(u).replace("http://", "").replace("https://", ""),
                    "clicks": row.cnt,
                })

    return {
        "total_clicks": total_clicks,
        "active_links": active_links,
        "unique_visitors": len(unique_ips),
        "clicks_over_time": clicks_over_time,
        "top_links": top_links,
        "geo_points": _build_geo_points(all_clicks),
        "recent_clicks": _build_recent_clicks(all_clicks),
    }
