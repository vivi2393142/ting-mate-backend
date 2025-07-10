import random
import string
from datetime import datetime, timedelta
from typing import Optional

from nanoid import generate

from app.core.database import execute_query, execute_update
from app.schemas.invitation import Invitation, InvitationStatus


class InvitationRepository:
    """Repository for invitation data access operations"""

    @staticmethod
    def generate_invitation_code() -> str:
        """Generate a unique 8-character invitation code"""
        while True:
            # Generate 8-character code with uppercase letters and digits
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # Check if code already exists
            if not InvitationRepository.invitation_code_exists(code):
                return code

    @staticmethod
    def invitation_code_exists(code: str) -> bool:
        """Check if invitation code already exists"""
        try:
            query = "SELECT COUNT(*) as count FROM user_invitations WHERE invitation_code = %s"
            result = execute_query(query, (code,))
            return result[0]["count"] > 0 if result else False
        except Exception as e:
            print(f"Error checking invitation code existence: {e}")
            return False

    @staticmethod
    def create_invitation(inviter_id: str) -> Invitation:
        """Create a new invitation"""
        try:
            invitation_id = generate()
            invitation_code = InvitationRepository.generate_invitation_code()
            expires_at = datetime.now() + timedelta(hours=24)

            insert_sql = """
            INSERT INTO user_invitations (id, inviter_id, invitation_code, expires_at)
            VALUES (%s, %s, %s, %s)
            """

            execute_update(
                insert_sql, (invitation_id, inviter_id, invitation_code, expires_at)
            )

            return Invitation(
                id=invitation_id,
                inviter_id=inviter_id,
                invitation_code=invitation_code,
                status=InvitationStatus.PENDING,
                expires_at=expires_at,
                created_at=datetime.now(),
            )

        except Exception as e:
            raise ValueError(f"Failed to create invitation: {str(e)}")

    @staticmethod
    def get_invitation_by_code(code: str) -> Optional[Invitation]:
        """Get invitation by code"""
        try:
            query = """
            SELECT * FROM user_invitations 
            WHERE invitation_code = %s
            """

            result = execute_query(query, (code,))

            if result:
                row = result[0]
                return Invitation(
                    id=row["id"],
                    inviter_id=row["inviter_id"],
                    invitation_code=row["invitation_code"],
                    status=InvitationStatus(row["status"]),
                    expires_at=row["expires_at"],
                    created_at=row["created_at"],
                )

            return None

        except Exception as e:
            print(f"Error getting invitation by code: {e}")
            return None

    @staticmethod
    def get_invitation_info(code: str) -> Optional[dict]:
        """Get invitation info with inviter details"""
        try:
            query = """
            SELECT i.*, u.role as inviter_role, s.name as inviter_name
            FROM user_invitations i
            JOIN users u ON i.inviter_id = u.id
            JOIN user_settings s ON u.id = s.user_id
            WHERE i.invitation_code = %s
            """

            result = execute_query(query, (code,))

            if result:
                row = result[0]
                return {
                    "inviter_name": row["inviter_name"],
                    "inviter_role": row["inviter_role"],
                    "expires_at": row["expires_at"],
                    "status": row["status"],
                }

            return None

        except Exception as e:
            print(f"Error getting invitation info: {e}")
            return None

    @staticmethod
    def update_invitation_status(code: str, status: InvitationStatus) -> bool:
        """Update invitation status"""
        try:
            update_sql = """
            UPDATE user_invitations 
            SET status = %s 
            WHERE invitation_code = %s
            """

            result = execute_update(update_sql, (status.value, code))
            return result > 0

        except Exception as e:
            print(f"Error updating invitation status: {e}")
            return False

    @staticmethod
    def delete_invitation(code: str) -> bool:
        """Delete invitation"""
        try:
            delete_sql = """
            DELETE FROM user_invitations 
            WHERE invitation_code = %s
            """

            result = execute_update(delete_sql, (code,))
            return result > 0

        except Exception as e:
            print(f"Error deleting invitation: {e}")
            return False

    @staticmethod
    def get_user_invitations(user_id: str) -> list:
        """Get all invitations created by a user"""
        try:
            query = """
            SELECT * FROM user_invitations 
            WHERE inviter_id = %s 
            ORDER BY created_at DESC
            """

            results = execute_query(query, (user_id,))
            invitations = []

            for row in results:
                invitation = Invitation(
                    id=row["id"],
                    inviter_id=row["inviter_id"],
                    invitation_code=row["invitation_code"],
                    status=InvitationStatus(row["status"]),
                    expires_at=row["expires_at"],
                    created_at=row["created_at"],
                )
                invitations.append(invitation)

            return invitations

        except Exception as e:
            print(f"Error getting user invitations: {e}")
            return []

    @staticmethod
    def cleanup_expired_invitations() -> int:
        """Clean up expired invitations and return count of cleaned"""
        try:
            cleanup_sql = """
            UPDATE user_invitations 
            SET status = 'EXPIRED' 
            WHERE expires_at < NOW() AND status = 'PENDING'
            """

            result = execute_update(cleanup_sql)
            return result

        except Exception as e:
            print(f"Error cleaning up expired invitations: {e}")
            return 0
