import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

import app.services.user as user
from app.core.config import ALGORITHM, SECRET_KEY
from app.db.fake_db import fake_users_db
from app.schemas.auth import RegisterRequest
from app.schemas.user import User, UserDB
from app.services.security import get_password_hash

# TODO: replace with real database


def userdb_to_user(userdb: UserDB) -> User:
    return User(id=userdb.id, email=userdb.email, anonymous_id=userdb.anonymous_id)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return user.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_user(user_create: RegisterRequest) -> User:
    # Check for duplicate email
    for u in fake_users_db.values():
        if u.email == user_create.email:
            raise ValueError("Email already registered")
    # TODO: Check if match password rules
    hashed_password = get_password_hash(user_create.password)
    # If anonymous_id is provided, upgrade the anonymous user
    if hasattr(user_create, "anonymous_id") and user_create.anonymous_id:
        for u in fake_users_db.values():
            if u.anonymous_id == user_create.anonymous_id:
                u.email = user_create.email
                u.hashed_password = hashed_password
                return userdb_to_user(u)
    # Otherwise, create a new user
    user_id = str(uuid.uuid4())
    userdb = UserDB(
        id=user_id, email=user_create.email, hashed_password=hashed_password
    )
    fake_users_db[user_id] = userdb
    return userdb_to_user(userdb)


def get_user(
    value: str, by: Literal["id", "email", "anonymous_id"] = "id"
) -> UserDB | None:
    if by == "id":
        return fake_users_db.get(value)
    elif by == "email":
        for u in fake_users_db.values():
            if u.email == value:
                return u
    elif by == "anonymous_id":
        for u in fake_users_db.values():
            if u.anonymous_id == value:
                return u
    return None


def get_user_from_token(token: str) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            return None
        userdb = get_user(user_email, "email")
        if userdb:
            return userdb_to_user(userdb)
        return None
    except Exception:
        return None
