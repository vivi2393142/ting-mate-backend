from fastapi import Depends, HTTPException

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import get_route, post_route
from app.repositories.user import UserRepository
from app.repositories.user_locations import UserLocationsRepository
from app.schemas.user import Role, User
from app.schemas.user_locations import UserLocationCreate, UserLocationResponse


@get_route(
    path="/user/linked-location/{carereceiver_email}",
    summary="Get linked carereceiver's location",
    description="Caregiver queries the location of a linked carereceiver if both parties have enabled sharing.",
    response_model=UserLocationResponse,
    tags=["user_locations"],
)
def get_linked_location(
    carereceiver_email: str, user: User = Depends(get_current_user_or_create_anonymous)
):
    # Only caregiver can query linked carereceiver's location, and both parties must enable sharing
    if user.role != Role.CAREGIVER:
        raise HTTPException(
            status_code=403, detail="Only caregiver can use this endpoint."
        )
    # Find carereceiver by email
    carereceiver = UserRepository.get_user(carereceiver_email, by="email")
    if not carereceiver or carereceiver.role != Role.CARERECEIVER:
        raise HTTPException(status_code=404, detail="Carereceiver not found.")
    carereceiver_id = carereceiver.id
    # Check if linked
    links = UserRepository.get_user_links(user.id, user.role)
    if not any(link["email"] == carereceiver_email for link in links):
        raise HTTPException(status_code=403, detail="No linked carereceiver.")
    # Check if carereceiver enabled allow_share_location
    settings = UserRepository.get_user_settings(carereceiver_id)
    if not settings or not settings.get("allow_share_location"):
        raise HTTPException(
            status_code=403, detail="Carereceiver has not enabled location sharing."
        )
    # Check if caregiver enabled show_linked_location
    my_settings = UserRepository.get_user_settings(user.id)
    if not my_settings or not my_settings.get("show_linked_location"):
        raise HTTPException(
            status_code=403, detail="You have not enabled show_linked_location."
        )
    loc = UserLocationsRepository.get_location(carereceiver_id)
    if not loc:
        # If location not found but sharing is enabled, return 200 with null data
        return None
    return loc


@post_route(
    path="/user/location",
    summary="Update user location",
    description="Carereceiver uploads or updates their current location.",
    response_model=UserLocationResponse,
    tags=["user_locations"],
)
def update_location(
    location: UserLocationCreate,
    user: User = Depends(get_current_user_or_create_anonymous),
):
    # Only carereceiver can upload location, and allow_share_location must be True
    if user.role != Role.CARERECEIVER:
        raise HTTPException(
            status_code=403, detail="Only carereceiver can update location."
        )
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
