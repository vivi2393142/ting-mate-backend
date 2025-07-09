"""
User repository - handles all database operations for users
"""

from typing import Literal, Optional
from uuid import UUID

import mysql.connector

from app.core.database import execute_query, execute_update
from app.schemas.user import Role, User, UserDB, UserDisplayMode, UserTextSize
from app.services.security import get_password_hash


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
            INSERT IGNORE INTO user_settings (user_id, name, text_size, display_mode)
            VALUES (%s, %s, %s, %s)
            """
            execute_update(
                settings_sql,
                (user_create.id, "", UserTextSize.STANDARD, UserDisplayMode.FULL),
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
            INSERT INTO user_settings (user_id, name, text_size, display_mode)
            VALUES (%s, %s, %s, %s)
            """
            execute_update(
                settings_sql, (user_id, "", UserTextSize.STANDARD, UserDisplayMode.FULL)
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
