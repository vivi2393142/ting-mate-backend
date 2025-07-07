from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.api_decorator import get_route
from app.repositories.user import UserRepository
from app.schemas.user import User
from app.services.user import get_user

router = APIRouter()


@get_route(
    path="/user/me",
    summary="Get Current User",
    description="Get current authenticated user information.",
    response_model=User,
    tags=["user"],
)
def get_current_user_api(user=Depends(get_current_user)):
    return user


# TODO: Can only get linked user by email
@get_route(
    path="/user/{email}",
    summary="Get User by Email",
    description="Get user information by email.",
    response_model=User,
    tags=["user"],
)
def get_user_by_email(email: str):
    userdb = get_user(email, by="email")
    if not userdb:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRepository.userdb_to_user(userdb)
