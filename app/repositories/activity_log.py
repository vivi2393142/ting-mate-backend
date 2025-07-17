import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import execute_query, execute_update
from app.repositories.user import UserRepository
from app.schemas.activity_log import (
    Action,
    ActivityLog,
    ActivityLogCreate,
    is_personal_action,
    is_shared_action,
)
from app.schemas.user import Role


class ActivityLogRepository:
    """Repository for activity log operations"""

    # ==================== CORE DATABASE OPERATIONS ====================
    # Basic CRUD operations for activity logs

    @staticmethod
    def create_activity_log(activity_log: ActivityLogCreate) -> Optional[str]:
        """Create a new activity log entry"""
        try:
            log_id = str(uuid.uuid4())

            # Convert detail to JSON string if provided
            detail_json = None
            if activity_log.detail:
                detail_json = json.dumps(activity_log.detail, ensure_ascii=False)

            sql = """
            INSERT INTO activity_logs (id, user_id, target_user_id, action, detail, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            success = execute_update(
                sql,
                (
                    log_id,
                    activity_log.user_id,
                    activity_log.target_user_id,
                    activity_log.action.value,
                    detail_json,
                    datetime.now(),
                ),
            )

            return log_id if success else None

        except Exception as e:
            print(f"Error creating activity log: {e}")
            return None

    @staticmethod
    def log_activity(
        user_id: str,
        action: Action,
        target_user_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Convenience method to log an activity with validation"""
        # Validate action type and target_user_id consistency
        if is_personal_action(action) and target_user_id is not None:
            print(f"Warning: Personal action {action} should not have target_user_id")
            target_user_id = None
        elif is_shared_action(action) and target_user_id is None:
            print(f"Warning: Shared action {action} should have target_user_id")
            return None

        activity_log = ActivityLogCreate(
            user_id=user_id, target_user_id=target_user_id, action=action, detail=detail
        )
        return ActivityLogRepository.create_activity_log(activity_log)

    # ==================== QUERY OPERATIONS ====================
    # Methods for retrieving and filtering activity logs

    @staticmethod
    def get_linked_user_ids(user_id: str, user_role: Role) -> List[str]:
        """Get all linked user IDs for a user using UserRepository"""
        try:
            # Get linked users from UserRepository
            linked_users = UserRepository.get_user_links(user_id, user_role)

            # Extract user IDs by email lookup
            linked_user_ids = []
            for linked_user in linked_users:
                # Get user by email to get the ID
                user = UserRepository.get_user(linked_user["email"], by="email")
                if user:
                    linked_user_ids.append(user.id)

            return linked_user_ids

        except Exception as e:
            print(f"Error getting linked user IDs: {e}")
            return []

    @staticmethod
    def get_activity_logs(
        user_id: str,
        user_role: Role,
        actions: Optional[List[Action]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ActivityLog]:
        """Get activity logs for a user with linked users' shared operations"""
        try:
            # 1. Build SQL query
            final_sql, params = ActivityLogRepository._build_activity_logs_sql(
                user_id, user_role, actions, limit, offset, is_count=False
            )

            # 2. Execute unified query
            results = execute_query(final_sql, params)

            # 3. Process results
            logs = []
            for row in results:
                detail = None
                if row["detail"]:
                    try:
                        detail = json.loads(row["detail"])
                    except (json.JSONDecodeError, TypeError):
                        detail = None

                log = ActivityLog(
                    id=row["id"],
                    user_id=row["user_id"],
                    target_user_id=row["target_user_id"],
                    action=Action(row["action"]),
                    detail=detail,
                    timestamp=row["timestamp"],
                )
                logs.append(log)

            return logs

        except Exception as e:
            print(f"Error getting activity logs: {e}")
            return []

    @staticmethod
    def get_activity_logs_count(
        user_id: str,
        user_role: Role,
        actions: Optional[List[Action]] = None,
    ) -> int:
        """Get count of activity logs for a user with linked users' shared operations"""
        try:
            # 1. Build SQL query
            final_sql, params = ActivityLogRepository._build_activity_logs_sql(
                user_id, user_role, actions, is_count=True
            )

            # 2. Execute unified count query
            result = execute_query(final_sql, params)
            return (
                result[0]["total_count"] if result and result[0]["total_count"] else 0
            )

        except Exception as e:
            print(f"Error getting activity logs count: {e}")
            return 0

    # ==================== HELPER METHODS ====================
    # Internal utility methods for filtering and SQL building

    @staticmethod
    def _filter_actions_by_type(
        actions: List[Action], action_type: str
    ) -> List[Action]:
        """Filter actions by type (personal or shared)"""
        if action_type == "personal":
            return [action for action in actions if is_personal_action(action)]
        elif action_type == "shared":
            return [action for action in actions if is_shared_action(action)]
        return actions

    @staticmethod
    def _build_action_filter_sql(actions: List[Action]) -> tuple[str, List[str]]:
        """Build SQL action filter clause and parameters"""
        if not actions:
            return "", []

        action_values = [action.value for action in actions]
        placeholders = ", ".join(["%s"] * len(action_values))
        sql_clause = f" AND action IN ({placeholders})"
        return sql_clause, action_values

    @staticmethod
    def _build_activity_logs_sql(
        user_id: str,
        user_role: Role,
        actions: Optional[List[Action]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        is_count: bool = False,
    ) -> List[ActivityLog]:
        """Build SQL query for activity logs with parameters"""
        try:
            # 1. Get linked user IDs and add self to the list
            allowed_target_user_ids = ActivityLogRepository.get_linked_user_ids(
                user_id, user_role
            )
            allowed_target_user_ids.append(user_id)

            # 2. Filter actions by type
            shared_actions = ActivityLogRepository._filter_actions_by_type(
                actions or [], "shared"
            )
            personal_actions = ActivityLogRepository._filter_actions_by_type(
                actions or [], "personal"
            )

            # 3. Build unified SQL query parts
            sql_parts = []
            params = []

            # Select clause based on count or full query
            if is_count:
                select_clause = "SELECT COUNT(*) as count"
            else:
                select_clause = (
                    "SELECT id, user_id, target_user_id, action, detail, timestamp"
                )

            # 4. Build shared operations query if needed
            if shared_actions or actions is None:
                shared_sql = f"""
                {select_clause}
                FROM activity_logs
                WHERE target_user_id IN ({",".join(["%s"] * len(allowed_target_user_ids))})
                """
                shared_params = allowed_target_user_ids.copy()

                # Add action filter for shared actions
                if shared_actions:
                    action_clause, action_params = (
                        ActivityLogRepository._build_action_filter_sql(shared_actions)
                    )
                    shared_sql += action_clause
                    shared_params.extend(action_params)

                sql_parts.append(shared_sql)
                params.extend(shared_params)

            # 5. Build personal operations query if needed
            if personal_actions or actions is None:
                personal_sql = f"""
                {select_clause}
                FROM activity_logs
                WHERE user_id = %s AND target_user_id IS NULL
                """
                personal_params = [user_id]

                # Add action filter for personal actions
                if personal_actions:
                    action_clause, action_params = (
                        ActivityLogRepository._build_action_filter_sql(personal_actions)
                    )
                    personal_sql += action_clause
                    personal_params.extend(action_params)

                sql_parts.append(personal_sql)
                params.extend(personal_params)

            # 6. Combine queries with UNION
            if not sql_parts:
                return "", []

            if is_count:
                # For count, we need to sum the results from both queries
                final_sql = f"SELECT SUM(count) as total_count FROM ({' UNION ALL '.join(sql_parts)}) as combined_counts"
            else:
                # For regular query, union and order
                final_sql = f"({') UNION ALL ('.join(sql_parts)})"
                final_sql += " ORDER BY timestamp DESC"

                # Add limit and offset if provided
                if limit is not None and offset is not None:
                    final_sql += " LIMIT %s OFFSET %s"
                    params.append(limit)
                    params.append(offset)

            return final_sql, params

        except Exception as e:
            print(f"Error building activity logs SQL: {e}")
            return "", []

    # ==================== PERSONAL ACTION LOGGERS ====================
    # Specialized methods for logging personal operations (target_user_id = null)

    @staticmethod
    def log_user_settings_update(
        user_id: str, updated_fields: Dict[str, Any]
    ) -> Optional[str]:
        """Log user settings update"""
        detail = {
            "updated_fields": updated_fields,
            "description": f"Updated user settings: {', '.join(updated_fields.keys())}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id, action=Action.UPDATE_USER_SETTINGS, detail=detail
        )

    @staticmethod
    def log_user_link_add(
        user_id: str, linked_user_email: str, linked_user_name: str
    ) -> Optional[str]:
        """Log user link addition"""
        detail = {
            "linked_user_email": linked_user_email,
            "linked_user_name": linked_user_name,
            "description": f"Added link with {linked_user_name} ({linked_user_email})",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id, action=Action.ADD_USER_LINK, detail=detail
        )

    @staticmethod
    def log_user_link_remove(
        user_id: str, linked_user_email: str, linked_user_name: str
    ) -> Optional[str]:
        """Log user link removal"""
        detail = {
            "linked_user_email": linked_user_email,
            "linked_user_name": linked_user_name,
            "description": f"Removed link with {linked_user_name} ({linked_user_email})",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id, action=Action.REMOVE_USER_LINK, detail=detail
        )

    @staticmethod
    def log_role_transition(
        user_id: str, old_role: str, new_role: str
    ) -> Optional[str]:
        """Log user role transition"""
        detail = {
            "old_role": old_role,
            "new_role": new_role,
            "description": f"Role changed from {old_role} to {new_role}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id, action=Action.TRANSITION_USER_ROLE, detail=detail
        )

    # ==================== SHARED ACTION LOGGERS ====================
    # Specialized methods for logging shared operations (target_user_id required)

    @staticmethod
    def log_task_create(
        user_id: str, target_user_id: str, task_title: str, reminder_time: str
    ) -> Optional[str]:
        """Log task creation"""
        detail = {
            "task_title": task_title,
            "reminder_time": reminder_time,
            "description": f"Created task: {task_title} at {reminder_time}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.CREATE_TASK,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_task_update(
        user_id: str,
        target_user_id: str,
        task_title: str,
        updated_fields: Dict[str, Any],
    ) -> Optional[str]:
        """Log task update"""
        detail = {
            "task_title": task_title,
            "updated_fields": updated_fields,
            "description": f"Updated task '{task_title}': {', '.join(updated_fields.keys())}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.UPDATE_TASK,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_task_status_update(
        user_id: str, target_user_id: str, task_title: str, completed: bool
    ) -> Optional[str]:
        """Log task status update"""
        status = "completed" if completed else "uncompleted"
        detail = {
            "task_title": task_title,
            "status": status,
            "description": f"Marked task '{task_title}' as {status}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.UPDATE_TASK_STATUS,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_task_delete(
        user_id: str, target_user_id: str, task_title: str
    ) -> Optional[str]:
        """Log task deletion"""
        detail = {
            "task_title": task_title,
            "description": f"Deleted task: {task_title}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.DELETE_TASK,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_shared_note_create(
        user_id: str, target_user_id: str, note_title: str
    ) -> Optional[str]:
        """Log shared note creation"""
        detail = {
            "note_title": note_title,
            "description": f"Created shared note: {note_title}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.CREATE_SHARED_NOTE,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_shared_note_update(
        user_id: str,
        target_user_id: str,
        note_title: str,
        updated_fields: Dict[str, Any],
    ) -> Optional[str]:
        """Log shared note update"""
        detail = {
            "note_title": note_title,
            "updated_fields": updated_fields,
            "description": f"Updated shared note '{note_title}': {', '.join(updated_fields.keys())}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.UPDATE_SHARED_NOTE,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_shared_note_delete(
        user_id: str, target_user_id: str, note_title: str
    ) -> Optional[str]:
        """Log shared note deletion"""
        detail = {
            "note_title": note_title,
            "description": f"Deleted shared note: {note_title}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.DELETE_SHARED_NOTE,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_safe_zone_upsert(
        user_id: str, target_user_id: str, location_name: str, radius: int
    ) -> Optional[str]:
        """Log safe zone creation/update"""
        detail = {
            "location_name": location_name,
            "radius": radius,
            "description": f"Set safe zone at {location_name} with {radius}m radius",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.UPSERT_SAFE_ZONE,
            target_user_id=target_user_id,
            detail=detail,
        )

    @staticmethod
    def log_safe_zone_delete(
        user_id: str, target_user_id: str, location_name: str
    ) -> Optional[str]:
        """Log safe zone deletion"""
        detail = {
            "location_name": location_name,
            "description": f"Deleted safe zone at {location_name}",
        }
        return ActivityLogRepository.log_activity(
            user_id=user_id,
            action=Action.DELETE_SAFE_ZONE,
            target_user_id=target_user_id,
            detail=detail,
        )
