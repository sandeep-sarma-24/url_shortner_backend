from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.url import URL
from app.models.click import Click
from app.models.user import User
from app.utils.url_generator import generate_short_code
from app.utils.validators import is_valid_url, is_valid_slug
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.configs.config import get_settings

settings = get_settings()


def create_short_url(
    db: Session,
    original_url: str,
    custom_slug: str | None = None,
    title: str | None = None,
    user: User | None = None,
) -> URL:
    if not is_valid_url(original_url):
        raise BadRequestException("Invalid URL format")

    if custom_slug:
        if not is_valid_slug(custom_slug):
            raise BadRequestException("Slug must be 3-50 alphanumeric characters, hyphens, or underscores")
        existing = db.query(URL).filter((URL.short_code == custom_slug) | (URL.custom_slug == custom_slug)).first()
        if existing:
            raise ConflictException("This custom slug is already taken")
        short_code = custom_slug
    else:
        short_code = generate_short_code()
        while db.query(URL).filter(URL.short_code == short_code).first():
            short_code = generate_short_code()

    url = URL(
        original_url=original_url,
        short_code=short_code,
        custom_slug=custom_slug,
        title=title,
        user_id=user.id if user else None,
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


def get_url_by_short_code(db: Session, short_code: str) -> URL:
    url = db.query(URL).filter(
        (URL.short_code == short_code) | (URL.custom_slug == short_code)
    ).first()
    if not url:
        raise NotFoundException("Short URL not found")
    return url


def get_user_urls(
    db: Session,
    user: User,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
) -> tuple[list[URL], int]:
    query = db.query(URL).filter(URL.user_id == user.id)

    if search:
        query = query.filter(
            (URL.original_url.ilike(f"%{search}%"))
            | (URL.short_code.ilike(f"%{search}%"))
            | (URL.title.ilike(f"%{search}%"))
        )

    total = query.count()
    urls = query.order_by(URL.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return urls, total


def update_url(db: Session, url_id: int, user: User, is_active: bool | None = None, title: str | None = None) -> URL:
    url = db.query(URL).filter(URL.id == url_id, URL.user_id == user.id).first()
    if not url:
        raise NotFoundException("URL not found")
    if is_active is not None:
        url.is_active = is_active
    if title is not None:
        url.title = title
    db.commit()
    db.refresh(url)
    return url


def delete_url(db: Session, url_id: int, user: User) -> URL:
    url = db.query(URL).filter(URL.id == url_id, URL.user_id == user.id).first()
    if not url:
        raise NotFoundException("URL not found")
    db.delete(url)
    db.commit()
    return url


def record_click(
    db: Session,
    url: URL,
    ip_address: str | None = None,
    user_agent: str | None = None,
    referrer: str | None = None,
    country: str | None = None,
    country_code: str | None = None,
    region: str | None = None,
    city: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    isp: str | None = None,
    device_type: str | None = None,
    browser: str | None = None,
    os: str | None = None,
) -> Click:
    click = Click(
        url_id=url.id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        country=country,
        country_code=country_code,
        region=region,
        city=city,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        isp=isp,
        device_type=device_type,
        browser=browser,
        os=os,
    )
    db.add(click)
    db.commit()
    return click


def build_short_url(url: URL) -> str:
    slug = url.custom_slug or url.short_code
    return f"{settings.APP_URL}/{slug}"
