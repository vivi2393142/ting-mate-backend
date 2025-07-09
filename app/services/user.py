from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

import jwt

from app.core.config import settings
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.user import User, UserDB


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_user(user_create: RegisterRequest) -> User:
    # Validate id as UUID
    try:
        UUID(user_create.id)
    except Exception:
        raise ValueError("Invalid UUID format for user id")
    # Delegate all creation/upgrade logic to repository
    return UserRepository.create_user(user_create)


def get_user(value: str, by: Literal["id", "email"] = "id") -> UserDB | None:
    return UserRepository.get_user(value, by)


def create_anonymous_user(user_id: str) -> User:
    """Create a new anonymous user with provided id (must be valid UUID)"""
    try:
        UUID(user_id)
    except Exception:
        raise ValueError("Invalid UUID format for user id")
    return UserRepository.create_anonymous_user(user_id)


def get_user_from_token(token: str) -> User | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        userdb = UserRepository.get_user(user_id, "id")
        if userdb:
            return UserRepository.userdb_to_user(userdb)
        return None
    except Exception:
        return None
