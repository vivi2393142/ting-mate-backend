from fastapi import Depends

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route
from app.schemas.user import User


@get_route(
    path="/user/me",
    summary="Get Current User",
    description="Get current authenticated user information.",
    response_model=User,
    tags=["user"],
)
def get_current_user_api(user: User = Depends(get_current_user_or_create_anonymous)):
    return user
