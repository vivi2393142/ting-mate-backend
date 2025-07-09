from fastapi import Depends, HTTPException

from app.api.deps import get_current_user_or_create_anonymous, get_registered_user
from app.core.api_decorator import BaseResponse, get_route
from app.schemas.user import User
from app.services.user import get_user


@get_route(
    path="/user/me",
    summary="Get Current User",
    description="Get current authenticated user information.",
    response_model=User,
    tags=["user"],
)
def get_current_user_api(user: User = Depends(get_current_user_or_create_anonymous)):
    return user


# TODO: Can only get linked user by email
@get_route(
    path="/user/{email}",
    summary="Get User by Email (registered only)",
    description="Get user information by email. Only available for registered users.",
    response_model=BaseResponse,  # Return BaseResponse with email in data
    tags=["user"],
)
def get_user_by_email(email: str, user: User = Depends(get_registered_user)):
    userdb = get_user(email, by="email")
    if not userdb or not userdb.email:
        raise HTTPException(status_code=404, detail="User not found or not registered")
    return BaseResponse(
        success=True, message="Operation successful", data={"email": userdb.email}
    )
