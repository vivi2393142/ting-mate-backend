from app.schemas.user import Role
from app.services.link import LinkService


def get_actual_linked_carereceiver_id(user_id: str, user_role):
    """
    Get the actual carereceiver ID for a user.
    - If user is CARERECEIVER: return user_id (self)
    - If user is CAREGIVER: return linked carereceiver's ID (if exists)
    - Otherwise: return None
    """
    if user_role == Role.CARERECEIVER:
        return user_id
    elif user_role == Role.CAREGIVER:
        linked_carereceivers = LinkService.get_caregiver_links(user_id)
        if linked_carereceivers:
            return linked_carereceivers[0]["id"]
        else:
            return None
    else:
        return None
