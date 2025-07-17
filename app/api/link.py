from fastapi import Depends, HTTPException, Path

from app.api.deps import get_registered_user
from app.core.api_decorator import delete_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.user import UserRepository
from app.schemas.user import User
from app.services.link import LinkService


@delete_route(
    path="/user/links/{user_email}",
    summary="Remove User Link",
    description="Remove link with a specific user by email.",
    tags=["link"],
)
def remove_user_link(
    user_email: str = Path(..., description="The email of the user to unlink from"),
    user: User = Depends(get_registered_user),
):
    try:
        # Look up user id by email
        target_user = UserRepository.get_user(user_email, by="email")
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        target_user_id = target_user.id
        # Check if link exists
        if not LinkService.link_exists(user.id, target_user_id):
            raise HTTPException(status_code=404, detail="Link not found")
        # Remove the link
        success = LinkService.remove_link(user.id, target_user_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove link")

        # Log the user link removal
        ActivityLogRepository.log_user_link_remove(
            user_id=user.id,
            linked_user_email=target_user.email,
            linked_user_name=UserRepository.get_user_settings(target_user.id)["name"]
            or target_user.email,
        )

        return {"message": "Link removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
