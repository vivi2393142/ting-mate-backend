from typing import Optional

from app.core.database import execute_query, execute_update
from app.schemas.user_locations import UserLocationResponse


class UserLocationsRepository:
    @staticmethod
    def get_location(user_id: str) -> Optional[UserLocationResponse]:
        query = "SELECT * FROM user_locations WHERE id = %s"
        result = execute_query(query, (user_id,))
        if result:
            row = result[0]
            return UserLocationResponse(
                id=row["id"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                timestamp=row["timestamp"],
            )
        return None

    @staticmethod
    def upsert_location(user_id: str, latitude: float, longitude: float) -> bool:
        # MySQL upsert
        sql = """
        INSERT INTO user_locations (id, latitude, longitude, timestamp)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE latitude=VALUES(latitude), longitude=VALUES(longitude), timestamp=NOW()
        """
        return execute_update(sql, (user_id, latitude, longitude)) > 0
