import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import execute_query, execute_update
from app.schemas.notification import (
    NotificationCategory,
    NotificationData,
    NotificationLevel,
)


class NotificationRepository:
    """Repository for notification operations"""

    @staticmethod
    def create_notification(
        user_id: str,
        category: NotificationCategory,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
        level: NotificationLevel = NotificationLevel.GENERAL,
    ) -> Optional[str]:
        """Create a new notification"""
        try:
            notification_id = str(uuid.uuid4())
            sql = """
            INSERT INTO notifications (id, user_id, category, message, payload, level, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            success = execute_update(
                sql,
                (
                    notification_id,
                    user_id,
                    category.value,
                    message,
                    (
                        None
                        if payload is None
                        else json.dumps(payload, ensure_ascii=False)
                    ),
                    level.value,
                    False,
                    datetime.now(),
                ),
            )
            return notification_id if success else None
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None

    @staticmethod
    def get_notifications_by_user(
        user_id: str,
        category: Optional[NotificationCategory] = None,
        is_read: Optional[bool] = None,
        level: Optional[NotificationLevel] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[NotificationData]:
        """Get notifications for a user, with optional filters"""
        try:
            sql = "SELECT * FROM notifications WHERE user_id = %s"
            params = [user_id]
            if category:
                sql += " AND category = %s"
                params.append(category.value)
            if is_read is not None:
                sql += " AND is_read = %s"
                params.append(is_read)
            if level:
                sql += " AND level = %s"
                params.append(level.value)
            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            results = execute_query(sql, params)

            notifications = []
            for row in results:
                payload = row["payload"]
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        payload = None

                is_read = bool(row["is_read"])
                notification = NotificationData(
                    id=row["id"],
                    user_id=row["user_id"],
                    category=NotificationCategory(row["category"]),
                    message=row["message"],
                    payload=payload,
                    level=NotificationLevel(row["level"]),
                    is_read=is_read,
                    created_at=row["created_at"],
                )
                notifications.append(notification)
            return notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    @staticmethod
    def get_notifications_count_by_user(
        user_id: str,
        category: Optional[NotificationCategory] = None,
        is_read: Optional[bool] = None,
        level: Optional[NotificationLevel] = None,
    ) -> int:
        """Get total count of notifications for a user, with optional filters"""
        try:
            sql = "SELECT COUNT(*) as total_count FROM notifications WHERE user_id = %s"
            params = [user_id]
            if category:
                sql += " AND category = %s"
                params.append(category.value)
            if is_read is not None:
                sql += " AND is_read = %s"
                params.append(is_read)
            if level:
                sql += " AND level = %s"
                params.append(level.value)

            results = execute_query(sql, params)
            return results[0]["total_count"] if results else 0
        except Exception as e:
            print(f"Error getting notification count: {e}")
            return 0

    @staticmethod
    def get_notifications_by_id(
        notification_id: str,
    ) -> Optional[NotificationData]:
        """Get notification by id"""
        try:
            sql = "SELECT * FROM notifications WHERE id = %s LIMIT 1"
            params = [notification_id]
            results = execute_query(sql, params)

            target = results[0]
            if target:
                payload = target["payload"]
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        payload = None
                is_read = bool(target["is_read"])
                notification = NotificationData(
                    id=target["id"],
                    user_id=target["user_id"],
                    category=NotificationCategory(target["category"]),
                    message=target["message"],
                    payload=payload,
                    level=NotificationLevel(target["level"]),
                    is_read=is_read,
                    created_at=target["created_at"],
                )
                return notification
            return None
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    @staticmethod
    def mark_as_read(notification_id: str) -> bool:
        """Mark a notification as read"""
        try:
            sql = "UPDATE notifications SET is_read = TRUE WHERE id = %s"
            return execute_update(sql, (notification_id,))
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False

    @staticmethod
    def delete_notification(notification_id: str) -> bool:
        """Delete a notification by id"""
        try:
            sql = "DELETE FROM notifications WHERE id = %s"
            return execute_update(sql, (notification_id,))
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False

    @staticmethod
    def get_unread_count_by_user(user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            sql = "SELECT COUNT(*) as unread_count FROM notifications WHERE user_id = %s AND is_read = FALSE"
            results = execute_query(sql, (user_id,))
            return results[0]["unread_count"] if results else 0
        except Exception as e:
            print(f"Error getting unread notification count: {e}")
            return 0
