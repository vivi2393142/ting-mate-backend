from fastapi import Depends, HTTPException, Path

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import delete_route, get_route
from app.repositories.user import UserRepository
from app.schemas.user import User
from app.services.link import LinkService


@get_route(
    path="/user/links",
    summary="Get User Links",
    description="Get all linked users for the current user, including email and name.",
    tags=["link"],
)
def get_user_links(user: User = Depends(get_current_user_or_create_anonymous)):
    """Return all linked users with email and name."""
    try:
        links = LinkService.get_user_links(user.id, user.role)
        # Only include email and name in the response
        formatted_links = [
            {"email": link["email"], "name": link["name"]} for link in links
        ]
        return {"links": formatted_links}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@delete_route(
    path="/user/links/{user_email}",
    summary="Remove User Link",
    description="Remove link with a specific user by email.",
    tags=["link"],
)
def remove_user_link(
    user_email: str = Path(..., description="The email of the user to unlink from"),
    user: User = Depends(get_current_user_or_create_anonymous),
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
        return {"message": "Link removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
