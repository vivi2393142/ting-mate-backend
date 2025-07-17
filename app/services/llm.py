import json
import logging
from enum import Enum
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import settings
from app.repositories.llm_log import LLMLogRepository
from app.schemas.llm_log import LLMLogCreate
from app.schemas.task import RecurrenceUnit

logger = logging.getLogger(__name__)


class Status(str, Enum):
    CONFIRMED = "CONFIRMED"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"


# TODO: Add QUERY_TASK for querying task status or information
# Examples: "show my tasks", "what tasks do I have", "list reminders"
class IntentType(str, Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    DELETE_TASK = "DELETE_TASK"
    UNKNOWN = "UNKNOWN"


class IntentDetectionResult(BaseModel):
    intent_type: IntentType


class BaseTaskSlot(BaseModel):
    title: Optional[str] = None
    reminder_hour: Optional[int] = Field(None, ge=0, le=23)
    reminder_minute: Optional[int] = Field(None, ge=0, le=59)
    recurrence_unit: Optional[RecurrenceUnit] = Field(None)
    recurrence_interval: Optional[int] = Field(
        None, description="Must be between 1 and 30."
    )
    recurrence_days_of_week: Optional[List[int]] = Field(
        None, description="List of days of week for recurrence. 0=Monday, 6=Sunday."
    )
    recurrence_days_of_month: Optional[List[int]] = Field(
        None, description="List of days of month for recurrence. 1-31."
    )


class CreateTaskSlot(BaseTaskSlot):
    pass


class UpdateTaskSlot(BaseTaskSlot):
    task_id: Optional[str] = None
    completed: Optional[bool] = None


class CreateTaskResult(BaseModel):
    status: Status
    further_question: Optional[str] = None
    result: CreateTaskSlot


class UpdateTaskResult(BaseModel):
    status: Status
    further_question: Optional[str] = None
    result: UpdateTaskSlot


class TaskCandidate(BaseModel):
    task_id: str
    title: Optional[str] = None


class DeleteTaskResult(BaseModel):
    status: Status
    further_question: Optional[str] = None
    result: Optional[str] = None
    task_candidate_id_list: Optional[List[str]]


class LLMService:
    """Google Gemini LLM service"""

    # Common prompt components
    BASE_ROLE = "You are a voice assistant that helps users manage to-do tasks."
    SCHEMA_INSTRUCTION = (
        "Do not include any schema-related properties such as type, minimum, maximum, etc."
        "Only return a JSON object without any other text."
    )
    RECURRENCE_EXAMPLES = (
        "For recurrence rules, use these examples:\n"
        "- 'everyday' -> interval=1, unit=day\n"
        "- 'every week' -> interval=1, unit=week\n"
        "- 'every Tuesday and Sunday' -> interval=1, unit=week, days_of_week=[1,6]\n"
        "- 'every 2 weeks on Friday' -> interval=2, unit=week, days_of_week=[1,4]\n"
        "- 'every month on the 15th' -> interval=1, unit=month, days_of_month=[15]\n"
        "- 'every 3 months on the 1st and 15th' -> interval=3, unit=month, days_of_month=[1,15]\n"
    )
    TASK_SELECTION_BASE_WITH_CANDIDATES = (
        "Given 'user_input', 'task_candidates' and 'previous_result', "
        "identify which task the user wants to {action}. "
        "If you can confidently identify one task, set status to CONFIRMED and return its 'task_id' in the result"
        "(do not show this ID to the user)."
        "If you're not sure which task the user meant, set status to INCOMPLETE. In that case, "
        "provide a clear 'further_question' using only task titles (never mention task_id). "
        "Never use 'task_id' in any part of the message shown to the user."
    )
    TASK_SELECTION_BASE_WITH_ACTIVE_TASKS = (
        "Given 'user_input', 'active_tasks' and 'previous_response', "
        "identify which task the user wants to {action}. "
        "If you can confidently identify one task, take it out as 'task_id' in response schema."
        "If you're not sure which task the user meant, set status to INCOMPLETE. In that case, "
        "provide a clear 'further_question' using only task titles (never mention task_id). "
        "Never use 'task_id' in any part of the message shown to the user."
    )

    def __init__(self):
        self.intent_prompt = (
            f"{self.BASE_ROLE} "
            "Classify the user's intent into one of these categories:\n"
            "- CREATE_TASK: User wants to create a new task "
            "(e.g., 'remind me to', 'create a task', 'add a reminder')\n"
            "- UPDATE_TASK: User wants to modify an existing task "
            "(e.g., 'change the time', 'mark as done', 'update the title', 'complete this task')\n"
            "- DELETE_TASK: User wants to remove a task "
            "(e.g., 'delete this', 'remove the task')\n"
            "- UNKNOWN: Cannot determine the intent clearly\n"
            f"{self.SCHEMA_INSTRUCTION} "
            "user_input: {user_input}"
        )
        self.create_task_prompt = (
            f"{self.BASE_ROLE} "
            "Extract all required fields for creating a task. "
            "The user_input is the latest user input in text. "
            "'previous_response' is the last LLM output (if any); "
            "use both 'previous_response' and 'user_input' to update or complete the result. "
            "The required fields are: 'title', 'reminder_hour'. "
            "- If any required field is missing, set status to INCOMPLETE and provide a further_question. "
            "- If all required fields are present, set status to CONFIRMED and no further_question. "
            "- If fail to continue, set status to FAILED and no further_question. "
            "- If no 'reminder_minute' is provided, set it to 0."
            f"{self.SCHEMA_INSTRUCTION}\n"
            f"{self.RECURRENCE_EXAMPLES}"
            "user_input: {user_input}\n"
            "previous_response: {previous_response}\n"
        )
        self.update_task_prompt = (
            f"{self.BASE_ROLE} "
            "Extract all required fields for updating a task. "
            "The user_input is the latest user input in text. "
            "'previous_response' is the last LLM output (if any); "
            "use both 'previous_response' and 'user_input' to update or complete the result. "
            "The required field is: 'task_id' and one of any updated fields. "
            "- If task_id is missing, set status to INCOMPLETE and provide a further_question. "
            "- If task_id is present and none of updated fields is present, set status to INCOMPLETE and provide a 'further_question'. "  # noqa: E501
            "- If task_id is present and one of any updated fields is present, set status to CONFIRMED and no 'further_question'. "  # noqa: E501
            "- If fail to continue, set status to FAILED and no further_question. "
            "In order to find the 'task_id', you can follow this way:"
            f"{self.TASK_SELECTION_BASE_WITH_ACTIVE_TASKS.format(action='update')}"
            f"{self.SCHEMA_INSTRUCTION}\n"
            f"{self.RECURRENCE_EXAMPLES}"
            "active_tasks: {active_tasks}\n"
            "user_input: {user_input}\n"
            "previous_response: {previous_response}\n"
        )
        self.delete_task_prompt = (
            f"{self.BASE_ROLE} "
            f"{self.TASK_SELECTION_BASE_WITH_CANDIDATES.format(action='delete')} "
            f"{self.SCHEMA_INSTRUCTION}\n"
            "task_candidates: {task_candidates}\n"
            "user_input: {user_input}\n"
            "previous_result: {previous_result}\n"
        )

        self.intent_schema = IntentDetectionResult.model_json_schema()
        self.create_task_schema = CreateTaskResult.model_json_schema()
        self.update_task_schema = UpdateTaskResult.model_json_schema()
        self.delete_task_schema = DeleteTaskResult.model_json_schema()

    def generate_content(
        self,
        content: str,
        schema: dict,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        try:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model_name,
                contents=content,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )

            # Save successful conversation to database
            self._save_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                input_text=content,
                output_text=response.text,
            )

            return response.text

        except Exception:
            # Save failed conversation to database (output_text will be NULL)
            self._save_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                input_text=content,
                output_text=None,  # NULL for failed calls
            )

            # Re-raise the exception to maintain original behavior
            raise

    def _save_conversation(
        self,
        user_id: Optional[str],
        conversation_id: Optional[str],
        input_text: str,
        output_text: Optional[str],
    ):
        """Save LLM log to database"""
        try:
            log = LLMLogCreate(
                user_id=user_id,
                conversation_id=conversation_id,
                input_text=input_text,
                output_text=output_text,
            )
            LLMLogRepository.create_log(log)

        except Exception as e:
            logger.error(f"Failed to save LLM log: {e}")
            # Don't fail the main operation if saving fails

    async def detect_intent(
        self,
        user_input: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> IntentType:
        prompt = self.intent_prompt.format(user_input=user_input)
        response_text = self.generate_content(
            prompt,
            self.intent_schema,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        result = json.loads(response_text)
        return IntentType(result["intent_type"])

    async def extract_create_task(
        self,
        user_input: str,
        previous_response: Optional[str],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> CreateTaskResult:
        prompt = self.create_task_prompt.format(
            user_input=user_input, previous_response=previous_response
        )
        response_text = self.generate_content(
            prompt,
            self.create_task_schema,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        result = json.loads(response_text)
        return CreateTaskResult(**result)

    async def extract_update_task(
        self,
        active_tasks: str,
        user_input: str,
        previous_response: Optional[str],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> UpdateTaskResult:
        prompt = self.update_task_prompt.format(
            active_tasks=active_tasks,
            user_input=user_input,
            previous_response=previous_response,
        )
        response_text = self.generate_content(
            prompt,
            self.update_task_schema,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        result = json.loads(response_text)
        return UpdateTaskResult(**result)

    async def extract_delete_task(
        self,
        task_candidates: str,
        user_input: str,
        previous_response: Optional[str],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> DeleteTaskResult:
        prompt = self.delete_task_prompt.format(
            task_candidates=task_candidates,
            user_input=user_input,
            previous_response=previous_response,
        )
        response_text = self.generate_content(
            prompt,
            self.delete_task_schema,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        result = json.loads(response_text)
        return DeleteTaskResult(**result)


# Create global instance
llm_service = LLMService()
