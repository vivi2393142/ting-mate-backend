from fastapi import Depends, HTTPException

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route, post_route
from app.repositories.user import UserRepository
from app.repositories.user_locations import UserLocationsRepository
from app.schemas.user import User
from app.schemas.user_locations import UserLocationCreate, UserLocationResponse


@get_route(
    path="/user/linked-location/{target_email}",
    summary="Get linked user's location",
    description="Get location of a linked user if they have enabled location sharing.",
    response_model=UserLocationResponse,
    tags=["user_locations"],
)
def get_linked_location(
    target_email: str, user: User = Depends(get_current_user_or_create_anonymous)
):
    # Unregistered user cannot access location
    if not user.email:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Find target user by email
    target_user = UserRepository.get_user(target_email, by="email")
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check if linked (either as caregiver or carereceiver)
    links = UserRepository.get_user_links(user.id, user.role)
    if not any(link["email"] == target_email for link in links):
        raise HTTPException(status_code=403, detail="No linked user.")

    # Check if target user enabled allow_share_location
    target_settings = UserRepository.get_user_settings(target_user.id)
    if not target_settings or not target_settings.get("allow_share_location"):
        raise HTTPException(
            status_code=403, detail="User has not enabled location sharing."
        )

    loc = UserLocationsRepository.get_location(target_user.id)
    if not loc:
        # If location not found but sharing is enabled, return 200 with null data
        return None
    return loc


@post_route(
    path="/user/location",
    summary="Update user location",
    description="Upload or update current location if allow_share_location is enabled.",
    response_model=UserLocationResponse,
    tags=["user_locations"],
)
def update_location(
    location: UserLocationCreate,
    user: User = Depends(get_current_user_or_create_anonymous),
):
    # Unregistered user cannot update location
    if not user.email:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Check if user enabled allow_share_location
    settings = UserRepository.get_user_settings(user.id)
    if not settings or not settings.get("allow_share_location"):
        raise HTTPException(status_code=403, detail="Location sharing not enabled.")

    ok = UserLocationsRepository.upsert_location(
        user.id, location.latitude, location.longitude
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update location.")
    loc = UserLocationsRepository.get_location(user.id)
    return loc


@get_route(
    path="/user/can-get-location/{target_email}",
    summary="Check if current user can get target user's location",
    description=(
        "Return true if the current user is linked to the target user and "
        "the target user has enabled location sharing."
    ),
    response_model=bool,
    tags=["user_locations"],
)
def can_get_linked_location(
    target_email: str, user: User = Depends(get_current_user_or_create_anonymous)
):
    # Unregistered user cannot check
    if not user.email:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Find target user by email
    target_user = UserRepository.get_user(target_email, by="email")
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check if linked (either as caregiver or carereceiver)
    links = UserRepository.get_user_links(user.id, user.role)
    if not any(link["email"] == target_email for link in links):
        return False

    # Check if target user enabled allow_share_location
    target_settings = UserRepository.get_user_settings(target_user.id)
    if not target_settings or not target_settings.get("allow_share_location"):
        return False

    return True
