from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from app.core.config import settings
from app.repositories.user_repository import UserRepository
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
    # Check for duplicate email
    existing_user = UserRepository.get_user(user_create.email, "email")
    if existing_user:
        raise ValueError("Email already registered")

    # If anonymous_id is provided, check if anonymous user exists
    if hasattr(user_create, "anonymous_id") and user_create.anonymous_id:
        existing_anon_user = UserRepository.get_user(
            user_create.anonymous_id, "anonymous_id"
        )
        if existing_anon_user:
            # TODO: Implement anonymous user upgrade logic
            # For now, create new user
            pass

    # Create new user in database
    return UserRepository.create_user(user_create)


def get_user(
    value: str, by: Literal["id", "email", "anonymous_id"] = "id"
) -> UserDB | None:
    return UserRepository.get_user(value, by)


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
