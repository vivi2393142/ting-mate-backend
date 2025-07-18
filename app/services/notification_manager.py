import asyncio
import os
from typing import Optional

from app.api.notification import push_notification_to_sse
from app.repositories.notification import NotificationRepository
from app.repositories.user import UserRepository
from app.schemas.notification import NotificationCategory, NotificationLevel


class NotificationManager:
    @staticmethod
    def _create_and_push_notification(
        user_id: str,
        category: NotificationCategory,
        message: str,
        payload: dict,
        level: NotificationLevel = NotificationLevel.GENERAL,
    ):
        notification_id = NotificationRepository.create_notification(
            user_id=user_id,
            category=category,
            message=message,
            payload=payload,
            level=level,
        )
        # TODO: mock in testing
        if os.getenv("TESTING") != "true" and notification_id:
            notification = NotificationRepository.get_notifications_by_id(
                notification_id=notification_id
            )
            if notification:
                asyncio.create_task(push_notification_to_sse(user_id, notification))

    @staticmethod
    def _get_user_name(user_id: str) -> str:
        settings = UserRepository.get_user_settings(user_id)
        return settings["name"] if settings and settings.get("name") else "User"

    @staticmethod
    def _get_task_title(task_id: str) -> str:
        # Try to get task by id (search all users)
        # This assumes task_id is unique globally
        query = "SELECT title FROM tasks WHERE id = %s AND deleted = FALSE"
        from app.core.database import execute_query

        result = execute_query(query, (task_id,))
        if result and result[0].get("title"):
            return result[0]["title"]
        return "Task"

    @staticmethod
    def notify_safezone_warning(user_id: str, linked_user_id: str) -> Optional[str]:
        """Notify when a user leaves the safe zone (Warning level)"""
        name = NotificationManager._get_user_name(linked_user_id)
        message = f"{name} has left the safe zone."
        payload = {"linked_user_id": linked_user_id, "action": "SAFEZONE_LEFT"}
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.SAFEZONE,
            message=message,
            payload=payload,
            level=NotificationLevel.WARNING,
        )

    @staticmethod
    def notify_task_updated(
        user_id: str, linked_user_id: str, task_id: str
    ) -> Optional[str]:
        name = NotificationManager._get_user_name(linked_user_id)
        task_title = NotificationManager._get_task_title(task_id)
        message = f"{name} updated task: {task_title}."
        payload = {
            "linked_user_id": linked_user_id,
            "task_id": task_id,
            "action": "TASK_UPDATED",
        }
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.TASK,
            message=message,
            payload=payload,
            level=NotificationLevel.GENERAL,
        )

    @staticmethod
    def notify_task_deleted(
        user_id: str, linked_user_id: str, task_id: str
    ) -> Optional[str]:
        name = NotificationManager._get_user_name(linked_user_id)
        task_title = NotificationManager._get_task_title(task_id)
        message = f"{name} deleted task: {task_title}."
        payload = {
            "linked_user_id": linked_user_id,
            "task_id": task_id,
            "action": "TASK_DELETED",
        }
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.TASK,
            message=message,
            payload=payload,
            level=NotificationLevel.GENERAL,
        )

    @staticmethod
    def notify_task_created(
        user_id: str, linked_user_id: str, task_id: str
    ) -> Optional[str]:
        name = NotificationManager._get_user_name(linked_user_id)
        task_title = NotificationManager._get_task_title(task_id)
        message = f"{name} created a new task: {task_title}."
        payload = {
            "linked_user_id": linked_user_id,
            "task_id": task_id,
            "action": "TASK_CREATED",
        }
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.TASK,
            message=message,
            payload=payload,
            level=NotificationLevel.GENERAL,
        )

    @staticmethod
    def notify_task_completed(
        user_id: str, linked_user_id: str, task_id: str
    ) -> Optional[str]:
        name = NotificationManager._get_user_name(linked_user_id)
        task_title = NotificationManager._get_task_title(task_id)
        message = f"{name} marked {task_title} as done."
        payload = {
            "linked_user_id": linked_user_id,
            "task_id": task_id,
            "action": "TASK_COMPLETED",
        }
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.TASK,
            message=message,
            payload=payload,
            level=NotificationLevel.GENERAL,
        )

    @staticmethod
    def notify_linked_account(user_id: str, linked_user_id: str) -> Optional[str]:
        name = NotificationManager._get_user_name(linked_user_id)
        message = f"{name} linked with you on Ting Mate."
        payload = {"linked_user_id": linked_user_id, "action": "LINKED_ACCOUNT"}
        NotificationManager._create_and_push_notification(
            user_id=user_id,
            category=NotificationCategory.USER_SETTING,
            message=message,
            payload=payload,
            level=NotificationLevel.GENERAL,
        )
