from typing import Optional
from uuid import UUID

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
    id: Optional[str] = Query(None, description="User id (UUID) for anonymous access"),
):
    """
    Get current user or create anonymous user if needed.
    - If token provided: validate and return registered user (must have email)
    - If id provided: find existing or create new anonymous user (must not have email)
    - If neither provided: error
    - If both provided: error
    """
    if token and id:
        raise HTTPException(
            status_code=400,
            detail="Cannot provide both token and id. Use only one authentication method.",
        )
    if token:
        # Registered user with token
        user = get_user_from_token(token)
        if not user or not user.email:
            raise HTTPException(
                status_code=401, detail="Invalid token or not a registered user"
            )
        return user
    elif id:
        # Validate id as UUID
        try:
            UUID(id)
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid UUID format for user id"
            )
        # Check if user exists
        userdb = get_user(id, by="id")
        if userdb:
            if userdb.email:
                # If user has email, must use token
                raise HTTPException(
                    status_code=401,
                    detail="Registered user must use token authentication",
                )
            return UserRepository.userdb_to_user(userdb)
        else:
            # Create new anonymous user with provided id
            return create_anonymous_user(id)
    else:
        raise HTTPException(
            status_code=400, detail="Must provide either token or id (UUID)"
        )


def get_registered_user(token: str = Depends(oauth2_scheme)):
    """Get current registered user (must have valid token and email)."""
    user = get_user_from_token(token)
    if not user or not user.email:
        raise HTTPException(
            status_code=401, detail="Authentication required (registered user only)"
        )
    return user
