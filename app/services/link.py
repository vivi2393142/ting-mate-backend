from datetime import datetime
from typing import List, Optional

from app.repositories.invitation import InvitationRepository
from app.repositories.user import UserRepository
from app.schemas.invitation import InvitationStatus
from app.schemas.user import Role


class LinkService:
    """Service for user linking operations"""

    @staticmethod
    def validate_link_request(inviter_id: str, invitee_id: str) -> tuple[bool, str]:
        """
        Validate link request according to business rules
        Returns (is_valid, error_message)
        """
        try:
            # Get both users
            inviter = UserRepository.get_user(inviter_id, "id")
            invitee = UserRepository.get_user(invitee_id, "id")

            if not inviter or not invitee:
                return False, "One or both users not found"

            # Rule 1: Cannot link to self
            if inviter_id == invitee_id:
                return False, "Cannot link to yourself"

            # Rule 2: Cannot link same roles
            if inviter.role == invitee.role:
                return (
                    False,
                    f"Cannot link {inviter.role.value} to {invitee.role.value}",
                )

            # Rule 3: Caregiver can only link to one carereceiver
            if inviter.role == Role.CAREGIVER:
                existing_links = LinkService.get_caregiver_links(inviter_id)
                if existing_links:
                    return False, "Caregiver can only link to one carereceiver"

            # Rule 4: Check if link already exists
            if LinkService.link_exists(inviter_id, invitee_id):
                return False, "Link already exists"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def link_exists(user1_id: str, user2_id: str) -> bool:
        """Check if a link exists between two users"""
        try:
            from app.core.database import execute_query

            query = """
            SELECT COUNT(*) as count FROM user_links 
            WHERE (caregiver_id = %s AND carereceiver_id = %s) 
            OR (caregiver_id = %s AND carereceiver_id = %s)
            """

            result = execute_query(query, (user1_id, user2_id, user2_id, user1_id))
            return result[0]["count"] > 0 if result else False

        except Exception as e:
            print(f"Error checking link existence: {e}")
            return False

    @staticmethod
    def create_link(caregiver_id: str, carereceiver_id: str) -> bool:
        """Create a link between caregiver and carereceiver"""
        try:
            from app.core.database import execute_update

            # Ensure caregiver_id is actually a caregiver and carereceiver_id is a carereceiver
            caregiver = UserRepository.get_user(caregiver_id, "id")
            carereceiver = UserRepository.get_user(carereceiver_id, "id")

            if not caregiver or not carereceiver:
                return False

            if (
                caregiver.role != Role.CAREGIVER
                or carereceiver.role != Role.CARERECEIVER
            ):
                return False

            insert_sql = """
            INSERT INTO user_links (caregiver_id, carereceiver_id)
            VALUES (%s, %s)
            """

            result = execute_update(insert_sql, (caregiver_id, carereceiver_id))
            return result > 0

        except Exception as e:
            print(f"Error creating link: {e}")
            return False

    @staticmethod
    def remove_link(user1_id: str, user2_id: str) -> bool:
        """Remove link between two users"""
        try:
            from app.core.database import execute_update

            delete_sql = """
            DELETE FROM user_links 
            WHERE (caregiver_id = %s AND carereceiver_id = %s) 
            OR (caregiver_id = %s AND carereceiver_id = %s)
            """

            result = execute_update(
                delete_sql, (user1_id, user2_id, user2_id, user1_id)
            )
            return result > 0

        except Exception as e:
            print(f"Error removing link: {e}")
            return False

    @staticmethod
    def remove_all_links_for_user(user_id: str) -> bool:
        """Remove all links for a user (both as caregiver and carereceiver)"""
        try:
            from app.core.database import execute_update

            delete_sql = """
            DELETE FROM user_links 
            WHERE caregiver_id = %s OR carereceiver_id = %s
            """

            result = execute_update(delete_sql, (user_id, user_id))
            return result >= 0  # Return True even if no links were deleted

        except Exception as e:
            print(f"Error removing all links for user: {e}")
            return False

    @staticmethod
    def get_caregiver_links(caregiver_id: str) -> List[dict]:
        """Get all carereceivers linked to a caregiver"""
        try:
            from app.core.database import execute_query

            query = """
            SELECT u.id, u.email, s.name, u.role
            FROM user_links l
            JOIN users u ON l.carereceiver_id = u.id
            JOIN user_settings s ON u.id = s.user_id
            WHERE l.caregiver_id = %s
            """

            results = execute_query(query, (caregiver_id,))
            return list(results) if results else []

        except Exception as e:
            print(f"Error getting caregiver links: {e}")
            return []

    @staticmethod
    def get_carereceiver_links(carereceiver_id: str) -> List[dict]:
        """Get all caregivers linked to a carereceiver"""
        try:
            from app.core.database import execute_query

            query = """
            SELECT u.id, u.email, s.name, u.role
            FROM user_links l
            JOIN users u ON l.caregiver_id = u.id
            JOIN user_settings s ON u.id = s.user_id
            WHERE l.carereceiver_id = %s
            """

            results = execute_query(query, (carereceiver_id,))
            return list(results) if results else []

        except Exception as e:
            print(f"Error getting carereceiver links: {e}")
            return []

    @staticmethod
    def get_user_links(user_id: str, user_role: Role) -> List[dict]:
        """Get all linked users for a user based on their role"""
        if user_role == Role.CAREGIVER:
            return LinkService.get_caregiver_links(user_id)
        else:
            return LinkService.get_carereceiver_links(user_id)

    @staticmethod
    def accept_invitation(
        invitation_code: str, invitee_id: str
    ) -> tuple[bool, str, Optional[dict]]:
        """
        Accept an invitation and create link
        Returns (success, message, linked_user_info)
        """
        try:
            # Get invitation
            invitation = InvitationRepository.get_invitation_by_code(invitation_code)
            if not invitation:
                return False, "Invitation not found", None

            # Check if invitation is expired
            if invitation.expires_at < datetime.now():
                return False, "Invitation has expired", None

            # Check if invitation is already used
            if invitation.status != InvitationStatus.PENDING:
                return False, "Invitation has already been used", None

            # Validate link request
            is_valid, error_message = LinkService.validate_link_request(
                invitation.inviter_id, invitee_id
            )
            if not is_valid:
                return False, error_message, None

            # Create link
            inviter = UserRepository.get_user(invitation.inviter_id, "id")
            invitee = UserRepository.get_user(invitee_id, "id")

            # Determine which is caregiver and which is carereceiver
            if inviter.role == Role.CAREGIVER:
                caregiver_id = inviter.id
                carereceiver_id = invitee.id
            else:
                caregiver_id = invitee.id
                carereceiver_id = inviter.id

            # Create the link
            if not LinkService.create_link(caregiver_id, carereceiver_id):
                return False, "Failed to create link", None

            # Update invitation status
            InvitationRepository.update_invitation_status(
                invitation_code, InvitationStatus.ACCEPTED
            )

            # Get linked user info for response
            linked_user_info = {
                "id": inviter.id,
                "name": UserRepository.get_user_settings(inviter.id)["name"],
                "role": inviter.role.value,
            }

            return True, "Link created successfully", linked_user_info

        except Exception as e:
            return False, f"Error accepting invitation: {str(e)}", None
