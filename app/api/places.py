import requests
from fastapi import Depends, HTTPException

from app.api.deps import get_registered_user
from app.core.api_decorator import post_route
from app.core.config import settings
from app.repositories.user import UserRepository
from app.schemas.places import PlaceSearchRequest, PlaceSearchResponse
from app.schemas.user import User


@post_route(
    path="/places/search",
    summary="Search places by text",
    description=(
        "Proxy to Google Place Text Search (New) API. "
        "User must be authenticated, have linked account, and either self or linked must "
        "have allow_share_location enabled."
    ),
    response_model=PlaceSearchResponse,
    tags=["places"],
)
def place_search_api(
    req: PlaceSearchRequest,
    user: User = Depends(get_registered_user),
):
    # 1. User must have at least one linked account
    links = UserRepository.get_user_links(user.id, user.role)
    if not links:
        raise HTTPException(status_code=403, detail="No linked account.")

    # 2. Either the user or any linked account must have allow_share_location enabled
    self_settings = UserRepository.get_user_settings(user.id)
    allow_self = self_settings and self_settings.get("allow_share_location")
    allow_linked = False
    for link in links:
        linked_user = UserRepository.get_user(link["email"], by="email")
        if linked_user:
            linked_settings = UserRepository.get_user_settings(linked_user.id)
            if linked_settings and linked_settings.get("allow_share_location"):
                allow_linked = True
                break
    if not (allow_self or allow_linked):
        raise HTTPException(status_code=403, detail="No one enabled location sharing.")

    # 3. Call Google Place Text Search API
    params = {
        "query": req.query,
        "key": settings.google_place_api_key,
    }
    if req.language:
        params["language"] = req.language
    if req.region:
        params["region"] = req.region
    resp = requests.get(settings.google_place_search_api_url, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google API error.")
    data = resp.json()
    return PlaceSearchResponse(results=data)
