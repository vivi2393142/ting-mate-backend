from typing import Optional

from fastapi import Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from app.repositories.user import UserRepository
from app.services.user import get_user, get_user_from_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def get_current_user_or_anonymous(
    token: Optional[str] = Depends(oauth2_scheme),
    anonymous_id: Optional[str] = Query(None),
):
    if token:
        user = get_user_from_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    elif anonymous_id:
        userdb = get_user(anonymous_id, by="anonymous_id")
        if not userdb:
            raise HTTPException(status_code=404, detail="Anonymous user not found")
        return UserRepository.userdb_to_user(userdb)
    else:
        raise HTTPException(status_code=401, detail="No authentication provided")
