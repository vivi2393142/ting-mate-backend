from datetime import datetime, timedelta, timezone
import app.services.user as user

from app.schemas.user import User
from app.services.security import get_password_hash
from app.schemas.auth import RegisterRequest
from app.db.fake_db import fake_users_db
from app.core.config import SECRET_KEY, ALGORITHM


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return user.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_user(user_create: RegisterRequest) -> User:
    if user_create.email in fake_users_db:
        raise ValueError("Email already registered")
    hashed_password = get_password_hash(user_create.password)
    user = User(email=user_create.email, hashed_password=hashed_password)
    fake_users_db[user_create.email] = user
    # TODO: handle anonymous_id
    return user


def get_user(email: str) -> User | None:
    if email not in fake_users_db:
        return None
    return fake_users_db[email]
