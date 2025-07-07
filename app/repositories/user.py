"""
User repository - handles all database operations for users
"""

import uuid
from typing import Literal, Optional

from app.core.database import execute_query, execute_update
from app.schemas.user import User, UserDB
from app.services.security import get_password_hash


class UserRepository:
    """Repository for user data access operations"""

    @staticmethod
    def create_user(user_create) -> User:
        """Create a new user in database"""
        try:
            # Generate UUID for new user
            user_id = str(uuid.uuid4())

            # Hash password
            hashed_password = get_password_hash(user_create.password)

            # Insert user into database
            insert_sql = """
            INSERT INTO users (id, email, hashed_password, anonymous_id)
            VALUES (%s, %s, %s, %s)
            """

            execute_update(
                insert_sql,
                (user_id, user_create.email, hashed_password, user_create.anonymous_id),
            )

            # Create user settings
            settings_sql = """
            INSERT INTO user_settings (user_id, text_size, display_mode)
            VALUES (%s, %s, %s)
            """

            execute_update(settings_sql, (user_id, "STANDARD", "FULL"))

            # Return user object
            return User(
                id=user_id,
                email=user_create.email,
                anonymous_id=user_create.anonymous_id,
            )

        except Exception as e:
            raise ValueError(f"Failed to create user: {str(e)}")

    @staticmethod
    def get_user(
        value: str, by: Literal["id", "email", "anonymous_id"] = "id"
    ) -> Optional[UserDB]:
        """Get user from database"""
        try:
            if by == "id":
                query = "SELECT * FROM users WHERE id = %s"
            elif by == "email":
                query = "SELECT * FROM users WHERE email = %s"
            elif by == "anonymous_id":
                query = "SELECT * FROM users WHERE anonymous_id = %s"
            else:
                return None

            result = execute_query(query, (value,))

            if result:
                user_data = result[0]
                return UserDB(
                    id=user_data["id"],
                    email=user_data["email"],
                    hashed_password=user_data["hashed_password"],
                    anonymous_id=user_data["anonymous_id"],
                )

            return None

        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    @staticmethod
    def userdb_to_user(userdb: UserDB) -> User:
        """Convert UserDB to User"""
        return User(id=userdb.id, email=userdb.email, anonymous_id=userdb.anonymous_id)
