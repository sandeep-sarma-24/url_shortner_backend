from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_service import get_link_analytics, get_dashboard_stats
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_dashboard_stats(db, user.id)


@router.get("/links/{url_id}")
def link_analytics(
    url_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_link_analytics(db, url_id, user_id=user.id)
