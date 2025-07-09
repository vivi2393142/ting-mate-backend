from fastapi import Depends

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route
from app.repositories.user import UserRepository
from app.schemas.user import User, UserSettingsResponse


@get_route(
    path="/user/me",
    summary="Get Current User",
    description="Get current authenticated user information.",
    response_model=User,
    tags=["user"],
)
def get_current_user_api(user: User = Depends(get_current_user_or_create_anonymous)):
    return user


@get_route(
    path="/user/settings",
    summary="Get Current User Settings",
    description="Get current user's settings and linked users (email + name).",
    response_model=UserSettingsResponse,
    tags=["user"],
)
def get_current_user_settings_api(
    user: User = Depends(get_current_user_or_create_anonymous),
):
    settings = UserRepository.get_user_settings(user.id)
    if not settings:
        return None

    if not user.email:
        links = []
    else:
        links = UserRepository.get_user_links(user.id, user.role)
    settings_response = dict(settings)
    settings_response["links"] = links
    return UserSettingsResponse(**settings_response)
