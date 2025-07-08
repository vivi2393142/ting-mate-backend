import logging

from app.core.database import execute_update
from app.models.llm_log import LLMLogCreate

logger = logging.getLogger(__name__)


class LLMLogRepository:
    """Repository for LLM log records"""

    @staticmethod
    def create_log(log: LLMLogCreate) -> None:
        """Create a new LLM log record"""
        try:
            sql = """
            INSERT INTO llm_logs (user_id, conversation_id, input_text, output_text)
            VALUES (%s, %s, %s, %s)
            """

            execute_update(
                sql,
                (
                    log.user_id,
                    log.conversation_id,
                    log.input_text,
                    log.output_text,
                ),
            )

        except Exception as e:
            logger.error(f"Error creating LLM log: {e}")
            raise
