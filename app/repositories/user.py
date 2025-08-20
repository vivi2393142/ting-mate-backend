"""
User repository - handles all database operations for users
"""

import json
import logging
from typing import Literal, Optional
from uuid import UUID

import mysql.connector

from app.core.database import execute_query, execute_update
from app.schemas.user import Role, User, UserDB, UserDisplayMode, UserTextSize
from app.services.security import get_password_hash

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access operations"""

    @staticmethod
    def create_user(user_create) -> User:
        """Create a new user. The id is provided by frontend and must be a valid UUID."""
        try:
            # Validate id as UUID
            try:
                UUID(user_create.id)
            except Exception:
                raise ValueError("Invalid UUID format for user id")
            # Check for existing user by id
            existing = UserRepository.get_user(user_create.id, "id")
            # Hash password
            hashed_password = get_password_hash(user_create.password)
            if not existing:
                # Create new user
                insert_sql = """
                INSERT INTO users (id, email, hashed_password, role)
                VALUES (%s, %s, %s, %s)
                """
                try:
                    execute_update(
                        insert_sql,
                        (
                            user_create.id,
                            user_create.email,
                            hashed_password,
                            user_create.role,
                        ),
                    )
                except mysql.connector.IntegrityError as e:
                    if "Duplicate entry" in str(e) and "for key 'users.email'" in str(
                        e
                    ):
                        raise ValueError("Email already registered")
                    raise
            else:
                if existing.email:
                    # Already registered
                    raise ValueError("User id already registered")
                # Upgrade anonymous user: set email, hashed_password, role
                update_sql = """
                UPDATE users SET email=%s, hashed_password=%s, role=%s WHERE id=%s
                """
                try:
                    execute_update(
                        update_sql,
                        (
                            user_create.email,
                            hashed_password,
                            user_create.role,
                            user_create.id,
                        ),
                    )
                except mysql.connector.IntegrityError as e:
                    if "Duplicate entry" in str(e) and "for key 'users.email'" in str(
                        e
                    ):
                        raise ValueError("Email already registered")
                    raise
            # Ensure user settings exist (insert if not exists)
            settings_sql = """
            INSERT IGNORE INTO user_settings (user_id, name, text_size, display_mode, reminder)
            VALUES (%s, %s, %s, %s, %s)
            """
            initReminder = {
                "task_reminder": True,
                "overdue_reminder": {
                    "enabled": True,
                    "delay_minutes": 30,
                    "repeat": False,
                },
                "safe_zone_exit_reminder": False,
                "task_completion_notification": True,
                "task_change_notification": True,
            }
            initReminder_json = json.dumps(initReminder)
            logger.info(f"❤️ update settings {initReminder}")
            execute_update(
                settings_sql,
                (
                    user_create.id,
                    "",
                    UserTextSize.STANDARD,
                    UserDisplayMode.FULL,
                    initReminder_json,
                ),
            )
            # Return user object
            return User(
                id=user_create.id,
                email=user_create.email,
                role=user_create.role,
            )
        except Exception as e:
            raise ValueError(f"Failed to create or upgrade user: {str(e)}")

    @staticmethod
    def create_anonymous_user(user_id: str) -> User:
        """Create a new anonymous user in database. The id is provided by frontend and must be a valid UUID."""
        try:
            # Validate id as UUID
            try:
                UUID(user_id)
            except Exception:
                raise ValueError("Invalid UUID format for user id")
            # Check for duplicate id
            existing = UserRepository.get_user(user_id, "id")
            if existing:
                raise ValueError("User id already exists")

            logger.info("🤖 create_anonymous_user")
            # Insert anonymous user into database
            insert_sql = """
            INSERT INTO users (id, email, hashed_password, role)
            VALUES (%s, %s, %s, %s)
            """
            execute_update(
                insert_sql,
                (
                    user_id,
                    None,
                    None,
                    Role.CARERECEIVER,
                ),
            )
            # Create user settings
            settings_sql = """
            INSERT INTO user_settings (
                user_id, name, text_size, display_mode, 
                allow_share_location, reminder
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            initReminder = {
                "task_reminder": True,
                "overdue_reminder": {
                    "enabled": True,
                    "delay_minutes": 30,
                    "repeat": False,
                },
                "safe_zone_exit_reminder": False,
                "task_completion_notification": True,
                "task_change_notification": True,
            }
            initReminder_json = json.dumps(initReminder)

            logger.info(f"🤖initReminder_json: {initReminder_json}")

            execute_update(
                settings_sql,
                (
                    user_id,
                    "",
                    UserTextSize.STANDARD,
                    UserDisplayMode.FULL,
                    False,
                    initReminder_json,
                ),
            )
            # Return user object
            return User(
                id=user_id,
                email=None,
                role=Role.CARERECEIVER,
            )
        except Exception as e:
            raise ValueError(f"Failed to create anonymous user: {str(e)}")

    @staticmethod
    def get_user(value: str, by: Literal["id", "email"] = "id") -> Optional[UserDB]:
        """Get user from database by id or email only."""
        try:
            if by == "id":
                query = "SELECT * FROM users WHERE id = %s"
            elif by == "email":
                query = "SELECT * FROM users WHERE email = %s"
            else:
                return None
            result = execute_query(query, (value,))
            if result:
                user_data = result[0]
                role = None
                if user_data["role"]:
                    try:
                        role = Role(user_data["role"])
                    except ValueError:
                        # If role is not a valid enum value, set to None
                        role = None
                return UserDB(
                    id=user_data["id"],
                    email=user_data["email"],
                    hashed_password=user_data["hashed_password"],
                    role=role,
                )
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    @staticmethod
    def userdb_to_user(userdb: UserDB) -> User:
        """Convert UserDB to User."""
        return User(id=userdb.id, email=userdb.email, role=userdb.role)

    @staticmethod
    def get_user_settings(user_id: str) -> Optional[dict]:
        """Get user_settings for a user_id."""
        try:
            query = "SELECT * FROM user_settings WHERE user_id = %s"
            result = execute_query(query, (user_id,))
            if result:
                return result[0]
            return None
        except Exception as e:
            print(f"Error getting user_settings: {e}")
            return None

    @staticmethod
    def get_user_links(user_id: str, role: Role) -> list:
        """Get linked users' email and name for a user, depending on role."""
        try:
            if role == Role.CAREGIVER:
                # Caregiver: find all carereceivers
                query = """
                    SELECT u.email, s.name FROM user_links l
                    JOIN users u ON l.carereceiver_id = u.id
                    JOIN user_settings s ON s.user_id = u.id
                    WHERE l.caregiver_id = %s
                """
            else:
                # Carereceiver: find all caregivers
                query = """
                    SELECT u.email, s.name FROM user_links l
                    JOIN users u ON l.caregiver_id = u.id
                    JOIN user_settings s ON s.user_id = u.id
                    WHERE l.carereceiver_id = %s
                """
            result = execute_query(query, (user_id,))
            return list(result) if result else []
        except Exception as e:
            print(f"Error getting user_links: {e}")
            return []

    @staticmethod
    def update_user_settings(user_id: str, settings_update) -> bool:
        """Update user settings for a user_id."""
        try:
            # First check if user settings exist
            existing_settings = UserRepository.get_user_settings(user_id)

            if not existing_settings:
                # Create default settings if they don't exist
                create_sql = """
                INSERT INTO user_settings (user_id, name, text_size, display_mode)
                VALUES (%s, %s, %s, %s)
                """

                execute_update(
                    create_sql,
                    (user_id, "", UserTextSize.STANDARD, UserDisplayMode.FULL),
                )

            # Build dynamic update query based on provided fields
            update_fields = []
            update_values = []

            if settings_update.name is not None:
                update_fields.append("name = %s")
                update_values.append(settings_update.name)

            if settings_update.textSize is not None:
                update_fields.append("text_size = %s")
                update_values.append(settings_update.textSize)

            if settings_update.displayMode is not None:
                update_fields.append("display_mode = %s")
                update_values.append(settings_update.displayMode)

            if settings_update.reminder is not None:
                update_fields.append("reminder = %s")
                # Convert to JSON string for database storage
                update_values.append(json.dumps(settings_update.reminder))

            if settings_update.emergency_contacts is not None:
                update_fields.append("emergency_contacts = %s")
                # Convert Pydantic models to dict before JSON serialization
                contacts = [
                    c.model_dump() if hasattr(c, "model_dump") else c
                    for c in settings_update.emergency_contacts
                ]
                update_values.append(json.dumps(contacts))

            if settings_update.allow_share_location is not None:
                update_fields.append("allow_share_location = %s")
                update_values.append(settings_update.allow_share_location)

            if not update_fields:
                # No fields to update
                return True

            # Add user_id to values
            update_values.append(user_id)

            # Construct the update query
            update_sql = f"""
            UPDATE user_settings 
            SET {', '.join(update_fields)}
            WHERE user_id = %s
            """

            execute_update(update_sql, tuple(update_values))
            return True

        except Exception as e:
            print(f"Error updating user_settings: {e}")
            return False

    @staticmethod
    def get_linked_carereceivers(caregiver_id: str) -> list:
        """Get all carereceivers linked to a caregiver."""
        try:
            query = """
            SELECT u.id, u.email, s.name FROM user_links l
            JOIN users u ON l.carereceiver_id = u.id
            JOIN user_settings s ON s.user_id = u.id
            WHERE l.caregiver_id = %s
            """
            result = execute_query(query, (caregiver_id,))
            return list(result) if result else []
        except Exception as e:
            print(f"Error getting linked carereceivers: {e}")
            return []

    @staticmethod
    def update_user_role(user_id: str, new_role: Role) -> bool:
        """Update user role in database"""
        try:
            update_sql = """
            UPDATE users SET role = %s WHERE id = %s
            """
            result = execute_update(update_sql, (new_role.value, user_id))
            return result > 0
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False

    @staticmethod
    def get_group_user_ids(user_id: str, include_self: bool = False) -> list:
        """
        Get all user ids in the same group (the carereceiver and all linked caregivers).
        The user's role is determined automatically.
        If user is a caregiver, find their linked carereceiver, then get all caregivers linked to that carereceiver.
        If user is a carereceiver, get all caregivers linked to them, plus themselves.
        Returns a list of user ids (str).
        """
        try:
            user = UserRepository.get_user(user_id, "id")
            if not user or not user.role:
                return []
            role = user.role
            if role == Role.CAREGIVER:
                # Find the carereceiver linked to this caregiver
                query = "SELECT carereceiver_id FROM user_links WHERE caregiver_id = %s"
                result = execute_query(query, (user_id,))
                if not result:
                    return []
                carereceiver_id = result[0]["carereceiver_id"]
            else:
                carereceiver_id = user_id

            # Find all caregivers linked to this carereceiver
            caregivers_query = (
                "SELECT caregiver_id FROM user_links WHERE carereceiver_id = %s"
            )
            caregivers = execute_query(caregivers_query, (carereceiver_id,))
            caregiver_ids = (
                [row["caregiver_id"] for row in caregivers] if caregivers else []
            )

            # Include the carereceiver themselves
            user_ids = caregiver_ids + [carereceiver_id]

            # If include_self is False, exclude the user themselves
            if not include_self:
                user_ids = [uid for uid in user_ids if uid != user_id]

            return user_ids
        except Exception as e:
            print(f"Error getting group user ids: {e}")
            return []

    @staticmethod
    def get_group_users(user_id: str, include_self: bool = False) -> list:
        """
        Get all users in the same group (the carereceiver and all linked caregivers).
        The user's role is determined automatically.
        If user is a caregiver, find their linked carereceiver, then get all caregivers linked to that carereceiver.
        If user is a carereceiver, get all caregivers linked to them, plus themselves.
        Returns a list of dicts: {id, email, name}.
        """
        try:
            user_ids = UserRepository.get_group_user_ids(
                user_id, include_self=include_self
            )
            users = []
            for uid in user_ids:
                user = UserRepository.get_user(uid, "id")
                if user:
                    settings = UserRepository.get_user_settings(uid)
                    name = settings["name"] if settings and "name" in settings else None
                    users.append(
                        {
                            "id": user.id,
                            "email": user.email,
                            "name": name,
                            "role": user.role,
                        }
                    )
            return users
        except Exception as e:
            print(f"Error getting group users: {e}")
            return []
