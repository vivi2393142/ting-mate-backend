import json
from typing import Optional

from app.core.database import execute_query, execute_update
from app.schemas.user import SafeZone


class SafeZonesRepository:
    """Repository for safe zone data access operations"""

    @staticmethod
    def get_safe_zone(user_id: str) -> Optional[SafeZone]:
        """Get safe zone for a user."""
        try:
            query = "SELECT * FROM safe_zones WHERE user_id = %s"
            result = execute_query(query, (user_id,))
            if result:
                row = result[0]
                location_data = json.loads(row["location"])
                return SafeZone(
                    location=location_data,
                    radius=row["radius"],
                )
            return None
        except Exception as e:
            print(f"Error getting safe zone: {e}")
            return None

    @staticmethod
    def create_safe_zone(user_id: str, safe_zone: SafeZone, created_by: str) -> bool:
        """Create a new safe zone for a user."""
        try:
            insert_sql = """
            INSERT INTO safe_zones (user_id, location, radius, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s)
            """
            location_json = json.dumps(safe_zone.location.model_dump())
            result = execute_update(
                insert_sql,
                (
                    user_id,
                    location_json,
                    safe_zone.radius,
                    created_by,
                    created_by,
                ),
            )
            return result > 0
        except Exception as e:
            print(f"Error creating safe zone: {e}")
            return False

    @staticmethod
    def update_safe_zone(user_id: str, safe_zone: SafeZone, updated_by: str) -> bool:
        """Update safe zone for a user."""
        try:
            update_sql = """
            UPDATE safe_zones 
            SET location = %s, radius = %s, updated_by = %s, updated_at = NOW()
            WHERE user_id = %s
            """
            location_json = json.dumps(safe_zone.location.model_dump())
            result = execute_update(
                update_sql,
                (location_json, safe_zone.radius, updated_by, user_id),
            )
            return result > 0
        except Exception as e:
            print(f"Error updating safe zone: {e}")
            return False

    @staticmethod
    def upsert_safe_zone(
        user_id: str, safe_zone: SafeZone, user_id_operating: str
    ) -> bool:
        """Create or update safe zone for a user."""
        try:
            # Check if safe zone exists
            existing = SafeZonesRepository.get_safe_zone(user_id)
            if existing:
                return SafeZonesRepository.update_safe_zone(
                    user_id, safe_zone, user_id_operating
                )
            else:
                return SafeZonesRepository.create_safe_zone(
                    user_id, safe_zone, user_id_operating
                )
        except Exception as e:
            print(f"Error upserting safe zone: {e}")
            return False

    @staticmethod
    def delete_safe_zone(user_id: str) -> bool:
        """Delete safe zone for a user."""
        try:
            delete_sql = "DELETE FROM safe_zones WHERE user_id = %s"
            result = execute_update(delete_sql, (user_id,))
            return result >= 0  # Return True even if no safe zone was deleted
        except Exception as e:
            print(f"Error deleting safe zone: {e}")
            return False
