import json
import logging
from typing import Optional

from app.core.database import execute_query, execute_update
from app.models.assistant_pending_task import (
    AssistantPendingTaskCreate,
    AssistantPendingTaskResponse,
)

logger = logging.getLogger(__name__)


class AssistantPendingTaskRepository:
    """Repository for assistant pending task operations"""

    @staticmethod
    def create_pending_task(
        pending_task: AssistantPendingTaskCreate,
    ) -> AssistantPendingTaskResponse:
        """Create a new assistant pending task"""
        try:
            sql = """
            INSERT INTO assistant_pending_tasks (conversation_id, user_id, intent_type, task_data)
            VALUES (%s, %s, %s, %s)
            """

            execute_update(
                sql,
                (
                    pending_task.conversation_id,
                    pending_task.user_id,
                    pending_task.intent_type.value,
                    json.dumps(pending_task.task_data),
                ),
            )

            # Get the inserted record
            select_sql = """
            SELECT id, conversation_id, user_id, intent_type, task_data, created_at
            FROM assistant_pending_tasks
            WHERE id = LAST_INSERT_ID()
            """

            result = execute_query(select_sql)
            if result:
                row = result[0]
                return AssistantPendingTaskResponse(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    user_id=row["user_id"],
                    intent_type=row["intent_type"],
                    task_data=json.loads(row["task_data"]),
                    created_at=row["created_at"],
                )

            logger.error("Failed to retrieve created pending task record")
            return None

        except Exception as e:
            logger.error(f"Error creating assistant pending task: {e}")
            raise

    @staticmethod
    def get_pending_task_by_conversation_id(
        conversation_id: str,
    ) -> Optional[AssistantPendingTaskResponse]:
        """Get assistant pending task by conversation ID"""
        try:
            sql = """
            SELECT id, conversation_id, user_id, intent_type, task_data, created_at
            FROM assistant_pending_tasks
            WHERE conversation_id = %s
            """

            result = execute_query(sql, (conversation_id,))

            if result:
                row = result[0]
                return AssistantPendingTaskResponse(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    user_id=row["user_id"],
                    intent_type=row["intent_type"],
                    task_data=json.loads(row["task_data"]),
                    created_at=row["created_at"],
                )

            return None

        except Exception as e:
            logger.error(f"Error getting assistant pending task: {e}")
            return None

    @staticmethod
    def delete_pending_task(task_id: int) -> bool:
        """Delete an assistant pending task"""
        try:
            sql = "DELETE FROM assistant_pending_tasks WHERE id = %s"
            execute_update(sql, (task_id,))
            return True

        except Exception as e:
            logger.error(f"Error deleting assistant pending task: {e}")
            return False
