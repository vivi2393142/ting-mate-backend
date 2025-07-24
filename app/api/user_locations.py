from fastapi import Depends, HTTPException

from app.api.deps import get_registered_user
from app.core.api_decorator import get_route, post_route
from app.repositories.safe_zones import SafeZonesRepository
from app.repositories.user import UserRepository
from app.repositories.user_locations import UserLocationsRepository
from app.schemas.user import Role, User
from app.schemas.user_locations import (
    ShouldGetLocationResponse,
    UserLocationCreate,
    UserLocationResponse,
)
from app.services.location_utils import is_within_safe_zone
from app.services.notification_manager import NotificationManager
from app.services.reminder_utils import should_send_safe_zone_notification
from app.utils.safe_block import safe_block


@get_route(
    path="/user/linked-location/{target_email}",
    summary="Get linked user's location",
    description="Get location of a linked user if they have enabled location sharing.",
    response_model=UserLocationResponse,
    tags=["user_locations"],
)
def get_linked_location(target_email: str, user: User = Depends(get_registered_user)):
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
    user: User = Depends(get_registered_user),
):
    # Unregistered user cannot update location
    if not user.email:
        raise HTTPException(status_code=401, detail="Authentication required.")

    # Check if user enabled allow_share_location
    settings = UserRepository.get_user_settings(user.id)
    if not settings or not settings.get("allow_share_location"):
        raise HTTPException(status_code=403, detail="Location sharing not enabled.")

    # Get previous location
    previous_location = UserLocationsRepository.get_location(user.id)

    ok = UserLocationsRepository.upsert_location(
        user.id, location.latitude, location.longitude
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update location.")

    # Safely check safe zone and send notifications if needed
    with safe_block("safe zone notification"):
        _check_safe_zone_and_notify(
            user, location.latitude, location.longitude, previous_location
        )

    loc = UserLocationsRepository.get_location(user.id)
    return loc


def _check_safe_zone_and_notify(
    user: User, latitude: float, longitude: float, previous_location=None
):
    """Check if user is within safe zone and send notifications if not."""
    # Only check for carereceivers
    if user.role != Role.CARERECEIVER:
        return

    # Get user's safe zone
    safe_zone = SafeZonesRepository.get_safe_zone(user.id)
    if not safe_zone:
        return  # No safe zone set, no need to check

    # Check if user is within safe zone
    is_within = is_within_safe_zone(
        user_lat=latitude,
        user_lon=longitude,
        safe_zone_lat=safe_zone.location.latitude,
        safe_zone_lon=safe_zone.location.longitude,
        safe_zone_radius_meters=safe_zone.radius,
    )

    # If user is currently within safe zone, no need to check previous status
    if is_within:
        return

    previous_is_within = None

    if previous_location:
        # Check if previous location was within safe zone
        previous_is_within = is_within_safe_zone(
            user_lat=previous_location.latitude,
            user_lon=previous_location.longitude,
            safe_zone_lat=safe_zone.location.latitude,
            safe_zone_lon=safe_zone.location.longitude,
            safe_zone_radius_meters=safe_zone.radius,
        )

    # Determine if status changed (from inside to outside, or first time outside)
    status_changed = False
    if previous_is_within is None:
        # First time checking, notify if outside
        status_changed = True
    else:
        # Compare previous and current status
        status_changed = previous_is_within  # Inside -> Outside

    if status_changed:
        # Get linked caregivers
        links = UserRepository.get_user_links(user.id, user.role)
        for link in links:
            linked_user = UserRepository.get_user(link["email"], by="email")
            # Check if caregiver wants safe zone notifications
            if (
                linked_user
                and linked_user.role == Role.CAREGIVER
                and should_send_safe_zone_notification(linked_user.id)
            ):
                NotificationManager.notify_safezone_warning(
                    user_id=linked_user.id,
                    monitor_user_id=user.id,
                )


@get_route(
    path="/user/can-get-location/{target_email}",
    summary="Check if current user can get target user's location",
    description=(
        "Return true if the current user is linked to the target user and "
        "the target user has enabled location sharing."
    ),
    response_model=ShouldGetLocationResponse,
    tags=["user_locations"],
)
def can_get_linked_location(
    target_email: str, user: User = Depends(get_registered_user)
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
        return ShouldGetLocationResponse(can_get_location=False)

    # Check if target user enabled allow_share_location
    target_settings = UserRepository.get_user_settings(target_user.id)
    if not target_settings or not target_settings.get("allow_share_location"):
        return ShouldGetLocationResponse(can_get_location=False)

    return ShouldGetLocationResponse(can_get_location=True)
