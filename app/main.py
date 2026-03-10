import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.database import Base, engine
from app.db.session import get_db
from app.api.middleware.cors import setup_cors
from app.api.v1.routes import health, urls, analytics, auth
from app.services.url_service import get_url_by_short_code, record_click, build_short_url
from app.services.cache_service import get_cached_url, set_cached_url, init_redis, close_redis
from app.services.geo_service import get_client_ip, lookup_ip_location
from app.utils.helpers import parse_user_agent
from app.configs.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:    %(name)s - %(message)s",
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_redis()
    yield
    close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Shortr - URL Shortener API",
        description="Fast, reliable URL shortener with analytics",
        version="1.0.0",
        lifespan=lifespan,
    )

    setup_cors(app)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(urls.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")

    @app.get("/{short_code}")
    def redirect_url(short_code: str, request: Request, db: Session = Depends(get_db)):
        cached = get_cached_url(short_code)

        if cached:
            url_obj = get_url_by_short_code(db, short_code)
        else:
            url_obj = get_url_by_short_code(db, short_code)
            set_cached_url(short_code, url_obj.original_url)
            cached = url_obj.original_url

        ip = get_client_ip(request)
        ua_info = parse_user_agent(request.headers.get("user-agent"))
        geo_info = lookup_ip_location(ip)
        record_click(
            db,
            url=url_obj,
            ip_address=ip,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            **ua_info,
            **geo_info,
        )
        return RedirectResponse(url=cached, status_code=307)

    return app


app = create_app()
