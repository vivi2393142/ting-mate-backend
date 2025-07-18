import json

from app.repositories.user import UserRepository
from app.schemas.user import OverdueReminderSettings, ReminderSettings


def get_user_reminder_settings(user_id: str) -> ReminderSettings:
    """
    Get user's reminder settings from database.
    Returns default settings if not found or invalid.
    """
    try:
        settings = UserRepository.get_user_settings(user_id)
        if not settings or not settings.get("reminder"):
            return ReminderSettings()

        reminder_data = settings["reminder"]

        # Handle string JSON
        if isinstance(reminder_data, str):
            try:
                reminder_data = json.loads(reminder_data)
            except (json.JSONDecodeError, TypeError):
                return ReminderSettings()

        # Validate and parse reminder settings
        if not isinstance(reminder_data, dict):
            return ReminderSettings()

        # Extract settings with defaults - use snake_case keys
        # If any setting is invalid or missing, default to False (no notifications)
        task_reminder = reminder_data.get("task_reminder", False)
        overdue_reminder = reminder_data.get("overdue_reminder", {})
        safe_zone_exit_reminder = reminder_data.get("safe_zone_exit_reminder", False)
        task_completion_notification = reminder_data.get(
            "task_completion_notification", False
        )
        task_change_notification = reminder_data.get("task_change_notification", False)

        # Parse overdue reminder settings
        overdue_enabled = (
            overdue_reminder.get("enabled", False)
            if isinstance(overdue_reminder, dict)
            else False
        )
        overdue_delay = (
            overdue_reminder.get("delay_minutes", 30)
            if isinstance(overdue_reminder, dict)
            else 30
        )
        overdue_repeat = (
            overdue_reminder.get("repeat", False)
            if isinstance(overdue_reminder, dict)
            else False
        )

        return ReminderSettings(
            task_reminder=task_reminder,
            overdue_reminder=OverdueReminderSettings(
                enabled=overdue_enabled,
                delay_minutes=overdue_delay,
                repeat=overdue_repeat,
            ),
            safe_zone_exit_reminder=safe_zone_exit_reminder,
            task_completion_notification=task_completion_notification,
            task_change_notification=task_change_notification,
        )

    except Exception as e:
        print(f"Error parsing reminder settings for user {user_id}: {e}")
        return ReminderSettings()


def should_send_task_notification(user_id: str, notification_type: str) -> bool:
    """
    Check if a task-related notification should be sent based on user's reminder settings.

    Args:
        user_id: The user ID to check settings for
        notification_type: Type of notification ('create', 'update', 'complete', 'delete')

    Returns:
        bool: True if notification should be sent, False otherwise
    """
    settings = get_user_reminder_settings(user_id)

    if notification_type == "create":
        return settings.task_reminder
    elif notification_type == "update":
        return settings.task_change_notification
    elif notification_type == "complete":
        return settings.task_completion_notification
    elif notification_type == "delete":
        return settings.task_change_notification
    else:
        return True  # Default to sending for unknown types


def should_send_safe_zone_notification(user_id: str) -> bool:
    """
    Check if safe zone exit notification should be sent based on user's reminder settings.

    Args:
        user_id: The user ID to check settings for

    Returns:
        bool: True if notification should be sent, False otherwise
    """
    settings = get_user_reminder_settings(user_id)
    return settings.safe_zone_exit_reminder
