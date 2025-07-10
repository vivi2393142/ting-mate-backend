import json

from fastapi import Depends, HTTPException

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route, post_route, put_route
from app.repositories.user import UserRepository
from app.schemas.user import (
    Role,
    User,
    UserDisplayMode,
    UserLink,
    UserMeResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
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
        # Since user should have settings (created by get_current_user_or_create_anonymous),
        # if settings don't exist, it's a database error
        raise ValueError("User settings not found in database")

    # Get linked users (as array of UserLink)
    if not user.email:
        linked_list = []
    else:
        links = UserRepository.get_user_links(user.id, user.role)
        linked_list = [
            UserLink(email=link["email"], name=link["name"]) for link in links
        ]
    # Compose reminder (pass through or use default if missing)
    reminder = None
    if settings.get("reminder"):
        try:
            reminder = (
                json.loads(settings["reminder"])
                if isinstance(settings["reminder"], str)
                else settings["reminder"]
            )
        except (json.JSONDecodeError, TypeError):
            reminder = None

    # Compose settings object
    settings_obj = UserSettingsResponse(
        name=settings.get("name", ""),
        linked=linked_list,
        textSize=settings.get("text_size", UserTextSize.STANDARD),
        displayMode=settings.get("display_mode", UserDisplayMode.FULL),
        reminder=reminder,
    )
    # Compose and return user object
    return UserMeResponse(
        email=user.email,
        role=user.role,
        settings=settings_obj,
    )


@put_route(
    path="/user/settings",
    summary="Update User Settings",
    description="Update current user settings including name, text size, display mode, and reminder preferences.",
    response_model=UserMeResponse,
    tags=["user"],
)
def update_user_settings_api(
    settings_update: UserSettingsUpdateRequest,
    user: User = Depends(get_current_user_or_create_anonymous),
):
    # Update user settings in database
    success = UserRepository.update_user_settings(user.id, settings_update)
    if not success:
        raise ValueError("Failed to update user settings")

    # Return updated user information (same as get_current_user_api)
    settings = UserRepository.get_user_settings(user.id)
    if not settings:
        # Since user should have settings (created by get_current_user_or_create_anonymous),
        # if settings don't exist, it's a database error
        raise ValueError("User settings not found in database")

    # Get linked users (as array of UserLink)
    if not user.email:
        linked_list = []
    else:
        links = UserRepository.get_user_links(user.id, user.role)
        linked_list = [
            UserLink(email=link["email"], name=link["name"]) for link in links
        ]

    # Compose reminder (pass through or use default if missing)
    reminder = None
    if settings.get("reminder"):
        try:
            reminder = (
                json.loads(settings["reminder"])
                if isinstance(settings["reminder"], str)
                else settings["reminder"]
            )
        except (json.JSONDecodeError, TypeError):
            reminder = None

    # Compose settings object
    settings_obj = UserSettingsResponse(
        name=settings.get("name", ""),
        linked=linked_list,
        textSize=settings.get("text_size", UserTextSize.STANDARD),
        displayMode=settings.get("display_mode", UserDisplayMode.FULL),
        reminder=reminder,
    )

    # Compose and return user object
    return UserMeResponse(
        email=user.email,
        role=user.role,
        settings=settings_obj,
    )


@post_route(
    path="/user/role/transition",
    summary="Transition User Role",
    description="Transition user role from CARERECEIVER to CAREGIVER. This will remove all existing tasks and links.",
    tags=["user"],
)
def transition_user_role_api(
    user: User = Depends(get_current_user_or_create_anonymous),
):
    # Restriction 1: Only CARERECEIVER can transition
    if user.role != Role.CARERECEIVER:
        raise HTTPException(
            status_code=400, detail="Only CARERECEIVER can transition to CAREGIVER"
        )

    # Restriction 2: Only users without links can transition
    from app.services.link import LinkService

    existing_links = LinkService.get_carereceiver_links(user.id)
    if existing_links:
        raise HTTPException(
            status_code=400,
            detail="Cannot transition user with existing links. Please remove all links first.",
        )

    # Update user role in database
    success = UserRepository.update_user_role(user.id, Role.CAREGIVER)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to transition user role")

    # Remove all existing tasks for this user (since caregiver doesn't have own tasks)
    from app.repositories.task import TaskRepository

    TaskRepository.delete_all_tasks_for_user(user.id)

    # Remove all existing links for this user
    LinkService.remove_all_links_for_user(user.id)

    return {"message": "Operation successful"}
