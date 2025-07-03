from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.services.user import get_user, userdb_to_user

router = APIRouter()


@router.get("/user/me")
def get_current_user_api(user=Depends(get_current_user)):
    return user


# TODO: Can only get linked user by email
@router.get("/user/{email}")
def get_user_by_email(email: str):
    userdb = get_user(email, by="email")
    if not userdb:
        raise HTTPException(status_code=404, detail="User not found")
    return userdb_to_user(userdb)
