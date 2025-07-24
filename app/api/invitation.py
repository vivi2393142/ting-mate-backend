from fastapi import Depends, HTTPException, Path

from app.api.deps import get_registered_user
from app.core.api_decorator import delete_route, get_route, post_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.invitation import InvitationRepository
from app.schemas.invitation import (
    AcceptInvitationResponse,
    InvitationInfo,
    InvitationResponse,
    InvitationStatus,
)
from app.schemas.user import Role, User
from app.services.link import LinkService
from app.services.notification_manager import NotificationManager
from app.utils.safe_block import safe_block


@post_route(
    path="/user/invitations/generate",
    summary="Generate Invitation Code",
    description="Generate a new invitation code for linking accounts.",
    response_model=InvitationResponse,
    tags=["invitation"],
)
def generate_invitation(user: User = Depends(get_registered_user)):
    try:
        invitation = InvitationRepository.create_invitation(user.id)
        return InvitationResponse(
            invitation_code=invitation.invitation_code,
            qr_code_url=None,
            expires_at=invitation.expires_at,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@get_route(
    path="/user/invitations/{invitation_code}",
    summary="Get Invitation Info",
    description="Get information about an invitation code.",
    response_model=InvitationInfo,
    tags=["invitation"],
)
def get_invitation_info(
    invitation_code: str = Path(..., description="The invitation code"),
    user: User = Depends(get_registered_user),
):
    try:
        invitation_info = InvitationRepository.get_invitation_info(invitation_code)

        if not invitation_info:
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Check if invitation is expired
        from datetime import datetime

        if invitation_info["expires_at"] < datetime.now():
            raise HTTPException(status_code=400, detail="Invitation has expired")

        # Check if invitation is already used
        if invitation_info["status"] != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Invitation has already been used"
            )

        return InvitationInfo(
            inviter_name=invitation_info["inviter_name"],
            inviter_role=invitation_info["inviter_role"],
            expires_at=invitation_info["expires_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@post_route(
    path="/user/invitations/{invitation_code}/accept",
    summary="Accept Invitation",
    description="Accept an invitation and create a link between users.",
    response_model=AcceptInvitationResponse,
    tags=["invitation"],
)
def accept_invitation(
    invitation_code: str = Path(..., description="The invitation code"),
    user: User = Depends(get_registered_user),
):
    try:
        # Use current user as invitee
        invitee_id = user.id

        # Get invitation and inviter info
        invitation = InvitationRepository.get_invitation_by_code(invitation_code)
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
        from app.repositories.user import UserRepository

        inviter = UserRepository.get_user(invitation.inviter_id, by="id")
        if not inviter:
            raise HTTPException(status_code=404, detail="Inviter not found")
        invitee = user

        # --- Check both are carereceiver and no existing caregiver links ---
        if inviter.role != Role.CARERECEIVER or invitee.role != Role.CARERECEIVER:
            raise HTTPException(
                status_code=400,
                detail="Both inviter and invitee must be carereceiver at the time of acceptance",
            )

        # Check invitee has no linked caregiver
        invitee_links = LinkService.get_carereceiver_links(invitee.id)
        if invitee_links:
            raise HTTPException(
                status_code=400, detail="Invitee already has a linked caregiver"
            )
        # Set invitee role to CAREGIVER before linking
        update_success = UserRepository.update_user_role(invitee.id, Role.CAREGIVER)
        if not update_success:
            raise HTTPException(
                status_code=500, detail="Failed to update invitee role to CAREGIVER"
            )
        # Refresh invitee object after role update
        invitee = UserRepository.get_user(invitee.id, by="id")

        success, message, linked_user_info = LinkService.accept_invitation(
            invitation_code, invitee_id
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Log the user link addition for both users
        # For the invitee (current user)
        with safe_block("invitee link addition logging"):
            ActivityLogRepository.log_user_link_add(
                user_id=invitee.id,
                linked_user_email=inviter.email,
                linked_user_name=UserRepository.get_user_settings(inviter.id)["name"]
                or inviter.email,
            )

        # For the inviter
        with safe_block("inviter link addition logging"):
            ActivityLogRepository.log_user_link_add(
                user_id=inviter.id,
                linked_user_email=invitee.email,
                linked_user_name=UserRepository.get_user_settings(invitee.id)["name"]
                or invitee.email,
            )

        # Add notification for inviter
        with safe_block("inviter link addition notification"):
            NotificationManager.notify_linked_account(
                user_id=inviter.id,
                linked_user_id=invitee.id,
            )

        return AcceptInvitationResponse(message=message, linked_user=linked_user_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@delete_route(
    path="/user/invitations/{invitation_code}",
    summary="Cancel Invitation",
    description="Cancel an invitation (only the creator can cancel).",
    tags=["invitation"],
)
def cancel_invitation(
    invitation_code: str = Path(..., description="The invitation code"),
    user: User = Depends(get_registered_user),
):
    try:
        # Get invitation to check ownership
        invitation = InvitationRepository.get_invitation_by_code(invitation_code)

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Check if user is the creator of the invitation
        if invitation.inviter_id != user.id:
            raise HTTPException(
                status_code=403, detail="Only the invitation creator can cancel it"
            )

        # Delete the invitation
        success = InvitationRepository.delete_invitation(invitation_code)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel invitation")

        return {"message": "Invitation cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
