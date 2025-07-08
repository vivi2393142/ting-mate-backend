from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from app.repositories.user import UserRepository
from app.services.user import create_anonymous_user, get_user, get_user_from_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token (for registered users only)"""
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_current_user_or_create_anonymous(
    token: Optional[str] = Depends(oauth2_scheme),
    anonymous_id: Optional[str] = Query(None),
):
    """
    Get current user or create anonymous user if needed.
    - If token provided: validate and return registered user
    - If anonymous_id provided: find existing or create new anonymous user
    - If neither provided: create new anonymous user
    """
    if token:
        # Registered user with token
        user = get_user_from_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    elif anonymous_id:
        # Check if anonymous user exists
        userdb = get_user(anonymous_id, by="anonymous_id")
        if userdb:
            # Existing anonymous user
            return UserRepository.userdb_to_user(userdb)
        else:
            # Create new anonymous user with provided ID
            return create_anonymous_user(anonymous_id)
    else:
        # Create new anonymous user with auto-generated ID
        return create_anonymous_user()
