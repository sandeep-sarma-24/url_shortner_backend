from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.url_schema import URLCreate, URLResponse, URLUpdate, URLListResponse, ShortenResponse
from app.schemas.common import MessageResponse
from app.services.url_service import (
    create_short_url,
    get_url_by_short_code,
    get_user_urls,
    update_url,
    delete_url,
    record_click,
    build_short_url,
)
from app.services.cache_service import get_cached_url, set_cached_url, invalidate_cache
from app.utils.helpers import parse_user_agent, get_referrer_source
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/urls", tags=["urls"])


@router.post("", response_model=ShortenResponse, status_code=201)
def shorten_url(
    data: URLCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = create_short_url(
        db,
        original_url=data.original_url,
        custom_slug=data.custom_slug,
        title=data.title,
        user=user,
    )
    return ShortenResponse(
        id=url.id,
        original_url=url.original_url,
        short_url=build_short_url(url),
        short_code=url.slug,
        created_at=url.created_at,
    )


@router.get("", response_model=URLListResponse)
def list_urls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    urls, total = get_user_urls(db, user, page=page, per_page=per_page, search=search)
    items = []
    for u in urls:
        click_count = len(u.clicks) if u.clicks else 0
        items.append(URLResponse(
            id=u.id,
            original_url=u.original_url,
            short_code=u.short_code,
            custom_slug=u.custom_slug,
            title=u.title,
            short_url=build_short_url(u),
            is_active=u.is_active,
            total_clicks=click_count,
            created_at=u.created_at,
            updated_at=u.updated_at,
        ))
    return URLListResponse(items=items, total=total, page=page, per_page=per_page)


@router.put("/{url_id}", response_model=URLResponse)
def update(
    url_id: int,
    data: URLUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = update_url(db, url_id, user, is_active=data.is_active, title=data.title)
    invalidate_cache(url.short_code)
    if url.custom_slug:
        invalidate_cache(url.custom_slug)
    return URLResponse(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        custom_slug=url.custom_slug,
        title=url.title,
        short_url=build_short_url(url),
        is_active=url.is_active,
        total_clicks=url.total_clicks,
        created_at=url.created_at,
        updated_at=url.updated_at,
    )


@router.delete("/{url_id}", response_model=MessageResponse)
def remove(
    url_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = delete_url(db, url_id, user)
    invalidate_cache(url.short_code)
    if url.custom_slug:
        invalidate_cache(url.custom_slug)
    return MessageResponse(message="URL deleted successfully")
