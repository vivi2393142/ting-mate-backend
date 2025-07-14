import json

from fastapi import Body, Depends, HTTPException

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

    # Compose emergency_contacts (pass through or use default if missing)
    emergency_contacts = None
    if settings.get("emergency_contacts"):
        try:
            emergency_contacts = (
                json.loads(settings["emergency_contacts"])
                if isinstance(settings["emergency_contacts"], str)
                else settings["emergency_contacts"]
            )
            if not isinstance(emergency_contacts, list):
                emergency_contacts = None
        except (json.JSONDecodeError, TypeError):
            emergency_contacts = None

    # Compose safe_zone (pass through or use default if missing)
    safe_zone = None
    if settings.get("safe_zone"):
        try:
            safe_zone_raw = (
                json.loads(settings["safe_zone"])
                if isinstance(settings["safe_zone"], str)
                else settings["safe_zone"]
            )
            if safe_zone_raw is not None:
                from app.schemas.user import SafeZone

                safe_zone = SafeZone.model_validate(safe_zone_raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            safe_zone = None

    # Compose settings object
    settings_obj = UserSettingsResponse(
        name=settings.get("name", ""),
        linked=linked_list,
        textSize=settings.get("text_size", UserTextSize.STANDARD),
        displayMode=settings.get("display_mode", UserDisplayMode.FULL),
        reminder=reminder,
        emergency_contacts=emergency_contacts,
        safe_zone=safe_zone,
        allow_share_location=settings.get("allow_share_location", False),
        show_linked_location=settings.get("show_linked_location", False),
    )
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

    # Compose emergency_contacts (pass through or use default if missing)
    emergency_contacts = None
    if settings.get("emergency_contacts"):
        try:
            emergency_contacts = (
                json.loads(settings["emergency_contacts"])
                if isinstance(settings["emergency_contacts"], str)
                else settings["emergency_contacts"]
            )
            if not isinstance(emergency_contacts, list):
                emergency_contacts = None
        except (json.JSONDecodeError, TypeError):
            emergency_contacts = None

    # Compose safe_zone (pass through or use default if missing)
    safe_zone = None
    if settings.get("safe_zone"):
        try:
            safe_zone_raw = (
                json.loads(settings["safe_zone"])
                if isinstance(settings["safe_zone"], str)
                else settings["safe_zone"]
            )
            if safe_zone_raw is not None:
                from app.schemas.user import SafeZone

                safe_zone = SafeZone.model_validate(safe_zone_raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            safe_zone = None

    # Compose settings object
    settings_obj = UserSettingsResponse(
        name=settings.get("name", ""),
        linked=linked_list,
        textSize=settings.get("text_size", UserTextSize.STANDARD),
        displayMode=settings.get("display_mode", UserDisplayMode.FULL),
        reminder=reminder,
        emergency_contacts=emergency_contacts,
        safe_zone=safe_zone,
        allow_share_location=settings.get("allow_share_location", False),
        show_linked_location=settings.get("show_linked_location", False),
    )
    return UserMeResponse(
        email=user.email,
        role=user.role,
        settings=settings_obj,
    )


@post_route(
    path="/user/role/transition",
    summary="Transition User Role",
    description="Transition user role between CARERECEIVER and CAREGIVER. Only users without any links can transition.",
    tags=["user"],
)
def transition_user_role_api(
    user: User = Depends(get_current_user_or_create_anonymous),
    target_role: Role = Body(
        ...,
        embed=True,
        description="Target role: 'CAREGIVER' or 'CARERECEIVER'",
    ),
):
    from app.services.link import LinkService

    # If target_role is the same as current role, do nothing
    if user.role == target_role:
        return {"message": "Operation successful"}

    # Check if the user has any links (either as caregiver or carereceiver)
    links_as_caregiver = LinkService.get_caregiver_links(user.id)
    links_as_carereceiver = LinkService.get_carereceiver_links(user.id)
    if links_as_caregiver or links_as_carereceiver:
        raise HTTPException(
            status_code=400,
            detail="Cannot transition user with existing links. Please remove all links first.",
        )

    # Update the user role in the database
    success = UserRepository.update_user_role(user.id, target_role)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to transition user role")

    # Remove all tasks for this user (only carereceiver will have tasks, but this is safe for both roles)
    from app.repositories.task import TaskRepository

    TaskRepository.delete_all_tasks_for_user(user.id)

    # Remove all shared notes for this user (both as carereceiver and as creator)
    from app.repositories.shared_notes import SharedNotesRepository

    # Delete notes where user is the carereceiver
    SharedNotesRepository.delete_all_notes_for_carereceiver(user.id)

    # Delete notes where user is the creator (for any carereceiver)
    SharedNotesRepository.delete_all_notes_created_by_user(user.id)

    # Remove all links for this user (should be none, but just in case)
    LinkService.remove_all_links_for_user(user.id)

    return {"message": "Operation successful"}
