import json
import logging
from typing import Optional

from app.core.database import execute_query, execute_update
from app.schemas.assistant_conversation import (
    AssistantConversationCreate,
    AssistantConversationResponse,
    AssistantConversationUpdate,
)

logger = logging.getLogger(__name__)


class AssistantConversationRepository:
    """Repository for assistant conversation operations"""

    @staticmethod
    def create_conversation(
        conversation: AssistantConversationCreate,
    ) -> AssistantConversationResponse:
        """Create a new assistant conversation"""
        try:
            sql = """
            INSERT INTO assistant_conversations (conversation_id, user_id, intent_type, llm_result, turn_count)
            VALUES (%s, %s, %s, %s, %s)
            """

            execute_update(
                sql,
                (
                    conversation.conversation_id,
                    conversation.user_id,
                    conversation.intent_type,
                    (
                        json.dumps(conversation.llm_result)
                        if conversation.llm_result
                        else None
                    ),
                    conversation.turn_count,
                ),
            )

            return AssistantConversationRepository.get_conversation(
                conversation.conversation_id
            )

        except Exception as e:
            logger.error(f"Error creating assistant conversation: {e}")
            raise

    @staticmethod
    def get_conversation(
        conversation_id: str,
    ) -> Optional[AssistantConversationResponse]:
        """Get assistant conversation by conversation ID"""
        try:
            sql = """
            SELECT conversation_id, user_id, intent_type, llm_result, turn_count, created_at, updated_at
            FROM assistant_conversations
            WHERE conversation_id = %s
            """

            result = execute_query(sql, (conversation_id,))

            if result:
                row = result[0]
                return AssistantConversationResponse(
                    conversation_id=row["conversation_id"],
                    user_id=row["user_id"],
                    intent_type=row["intent_type"],
                    llm_result=(
                        json.loads(row["llm_result"]) if row["llm_result"] else None
                    ),
                    turn_count=row["turn_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            return None

        except Exception as e:
            logger.error(f"Error getting assistant conversation: {e}")
            return None

    @staticmethod
    def update_conversation(
        conversation_id: str, updates: AssistantConversationUpdate
    ) -> Optional[AssistantConversationResponse]:
        """Update assistant conversation"""
        try:
            update_fields = []
            update_values = []

            if updates.intent_type is not None:
                update_fields.append("intent_type = %s")
                update_values.append(updates.intent_type)

            if updates.llm_result is not None:
                update_fields.append("llm_result = %s")
                update_values.append(json.dumps(updates.llm_result))

            if updates.turn_count is not None:
                update_fields.append("turn_count = %s")
                update_values.append(updates.turn_count)

            if not update_fields:
                return AssistantConversationRepository.get_conversation(conversation_id)

            sql = f"""
            UPDATE assistant_conversations
            SET {', '.join(update_fields)}
            WHERE conversation_id = %s
            """

            update_values.append(conversation_id)
            execute_update(sql, tuple(update_values))

            return AssistantConversationRepository.get_conversation(conversation_id)

        except Exception as e:
            logger.error(f"Error updating assistant conversation: {e}")
            return None

    @staticmethod
    def delete_conversation(conversation_id: str) -> bool:
        """Delete an assistant conversation"""
        try:
            sql = "DELETE FROM assistant_conversations WHERE conversation_id = %s"
            execute_update(sql, (conversation_id,))
            return True

        except Exception as e:
            logger.error(f"Error deleting assistant conversation: {e}")
            return False

    @staticmethod
    def cleanup_old_conversations(days: int = 7) -> int:
        """Clean up old assistant conversations"""
        try:
            sql = """
            DELETE FROM assistant_conversations 
            WHERE updated_at < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            result = execute_update(sql, (days,))
            return result

        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            return 0
