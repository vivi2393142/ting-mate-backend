from fastapi import Depends, HTTPException

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import delete_route, get_route, post_route
from app.repositories.safe_zones import SafeZonesRepository
from app.repositories.user import UserRepository
from app.schemas.user import Role, SafeZone, User


def _check_safe_zone_permission(requester, target_user):
    """
    Only allow carereceiver to access their own safe zone, or caregiver to access/edit linked carereceiver's safe zone.
    """
    if (
        requester.id == target_user.id
        and requester.role == target_user.role == Role.CARERECEIVER
    ):
        return True
    if requester.role == Role.CAREGIVER and target_user.role == Role.CARERECEIVER:
        # Caregiver must be linked to the target carereceiver
        links = UserRepository.get_user_links(requester.id, requester.role)
        if any(link["email"] == target_user.email for link in links):
            return True
    return False


@get_route(
    path="/safe-zone/{target_email}",
    summary="Get Safe Zone",
    description="Get safe zone for the target user (by email).",
    response_model=SafeZone,
    tags=["safe_zones"],
)
def get_safe_zone_api(
    target_email: str, user: User = Depends(get_current_user_or_create_anonymous)
):
    target_user = UserRepository.get_user(target_email, by="email")
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    if not _check_safe_zone_permission(user, target_user):
        raise HTTPException(
            status_code=403, detail="No permission to access this user's safe zone"
        )
    safe_zone = SafeZonesRepository.get_safe_zone(target_user.id)
    if not safe_zone:
        raise HTTPException(status_code=404, detail="Safe zone not found")
    return safe_zone


@post_route(
    path="/safe-zone/{target_email}",
    summary="Upsert Safe Zone",
    description="Create or update safe zone for the target user (by email). If the safe zone does not exist, it will be created.",
    response_model=SafeZone,
    tags=["safe_zones"],
)
def upsert_safe_zone_api(
    target_email: str,
    safe_zone: SafeZone,
    user: User = Depends(get_current_user_or_create_anonymous),
):
    target_user = UserRepository.get_user(target_email, by="email")
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    # --- Permission logic (same as before) ---
    if user.role == Role.CARERECEIVER and target_user.role == Role.CARERECEIVER:
        if user.id == target_user.id:
            pass
        else:
            raise HTTPException(
                status_code=403, detail="No permission to update this user's safe zone"
            )
    elif user.role == Role.CAREGIVER:
        if target_user.role != Role.CARERECEIVER:
            raise HTTPException(
                status_code=404, detail="Target user is not a carereceiver"
            )
        links = UserRepository.get_user_links(user.id, user.role)
        if not any(link["email"] == target_user.email for link in links):
            raise HTTPException(status_code=404, detail="No linked carereceiver found")
    else:
        raise HTTPException(
            status_code=403, detail="No permission to update this user's safe zone"
        )
    # --- Upsert logic ---
    success = SafeZonesRepository.upsert_safe_zone(target_user.id, safe_zone, user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upsert safe zone")
    return safe_zone


@delete_route(
    path="/safe-zone/{target_email}",
    summary="Delete Safe Zone",
    description="Delete safe zone for the target user (by email).",
    tags=["safe_zones"],
)
def delete_safe_zone_api(
    target_email: str, user: User = Depends(get_current_user_or_create_anonymous)
):
    target_user = UserRepository.get_user(target_email, by="email")
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    if not _check_safe_zone_permission(user, target_user):
        raise HTTPException(
            status_code=403, detail="No permission to delete this user's safe zone"
        )
    success = SafeZonesRepository.delete_safe_zone(target_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete safe zone")
    return {"message": "Safe zone deleted successfully"}
