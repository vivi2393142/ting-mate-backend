from fastapi import Depends

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route
from app.repositories.user import UserRepository
from app.schemas.user import (
    User,
    UserDisplayMode,
    UserLink,
    UserMeResponse,
    UserSettingsResponse,
    UserTextSize,
)


@get_route(
    path="/user/me",
    summary="Get Current User",
    description="Get current authenticated user information with settings.",
    response_model=UserMeResponse,
    tags=["user"],
)
def get_current_user_api(user: User = Depends(get_current_user_or_create_anonymous)):
    # Get user settings from DB
    settings = UserRepository.get_user_settings(user.id)
    if not settings:
        # If no settings found, return minimal user info
        return UserMeResponse(
            email=user.email,
            role=user.role,
            settings=UserSettingsResponse(
                name="",
                linked=[],
                textSize=UserTextSize.STANDARD,
                displayMode=UserDisplayMode.FULL,
                reminder=None,
            ),
        )
    # Get linked users (as array of UserLink)
    if not user.email:
        linked_list = []
    else:
        links = UserRepository.get_user_links(user.id, user.role)
        linked_list = [
            UserLink(email=link["email"], name=link["name"]) for link in links
        ]
    # Compose reminder (pass through or use default if missing)
    reminder = settings.get("reminder") or None
    # Compose settings object
    settings_obj = UserSettingsResponse(
        name=settings.get("name", ""),
        linked=linked_list,
        textSize=settings.get("text_size", "STANDARD"),
        displayMode=settings.get("display_mode", "FULL"),
        reminder=reminder,
    )
    # Compose and return user object
    return UserMeResponse(
        email=user.email,
        role=user.role,
        settings=settings_obj,
    )
