from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
