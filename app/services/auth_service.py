from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException


def register_user(db: Session, name: str, email: str, password: str) -> tuple[User, str]:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ConflictException("Email already registered")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    token = create_access_token(data={"sub": str(user.id)})
    return user, token


def update_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise BadRequestException("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    db.commit()


def update_profile(db: Session, user: User, name: str | None = None, email: str | None = None) -> User:
    if email and email != user.email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ConflictException("Email already taken")
        user.email = email
    if name:
        user.name = name
    db.commit()
    db.refresh(user)
    return user
