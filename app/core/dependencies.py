from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise UnauthorizedException()
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException()
    sub = payload.get("sub")
    if sub is None:
        raise UnauthorizedException()
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        raise UnauthorizedException()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedException()
    return user


def get_optional_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        return None
    return db.query(User).filter(User.id == user_id).first()
