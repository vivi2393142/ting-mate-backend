import json
import logging
import uuid
from typing import Any, Dict, Optional

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Google Gemini LLM service"""

    def __init__(self):
        # Only initialize Google Cloud services if not in test environment
        if settings.environment != "test":
            # Initialize Vertex AI
            aiplatform.init(
                project=settings.google_cloud_project_id,
                location=settings.vertex_ai_location,
            )

            # Create Gemini model
            self.model = GenerativeModel(settings.vertex_ai_model_name)
        else:
            # In test environment, set model to None
            self.model = None
            logger.info(
                "LLM service initialized in test mode - Google Cloud services disabled"
            )

        # Default prompt template
        self.base_prompt = """
You are an assistant helping users manage daily tasks through natural language voice commands.

You can understand the user's intent, extract required parameters, and map the command to one of the predefined structured task operations.

There are five available task operations:
1. CREATE a task
2. DELETE a task
3. UPDATE a task
4. COMPLETE a task
5. QUERY tasks

Each operation has a set of required and optional parameters. If any required parameter is missing, ask follow-up questions to clarify. Always use polite and concise language for follow-ups. Some actions require confirmation before execution — in that case, wait for confirmation before responding with the final answer.

Respond in this format:
{
  "conversationId": "string",
  "intentId": "CREATE_TASK|DELETE_TASK|UPDATE_TASK|COMPLETE_TASK|QUERY_TASKS|UNKNOWN",
  "status": "confirmed|incomplete|unknown",
  "parameters": { ... },
  "message": "User-facing response"
}

The intentId and parameter definitions are as follows:

CREATE_TASK:
  - title (required): string
  - description (optional): string
  - due_date (optional): string (YYYY-MM-DD format)
  - priority (optional): "low"|"medium"|"high"

DELETE_TASK:
  - task_id (required): string
  - title (optional): string (for confirmation)

UPDATE_TASK:
  - task_id (required): string
  - title (optional): string
  - description (optional): string
  - due_date (optional): string (YYYY-MM-DD format)
  - priority (optional): "low"|"medium"|"high"
  - status (optional): "pending"|"in_progress"|"completed"

COMPLETE_TASK:
  - task_id (required): string
  - title (optional): string (for confirmation)

QUERY_TASKS:
  - status (optional): "pending"|"in_progress"|"completed"
  - priority (optional): "low"|"medium"|"high"
  - limit (optional): number (default: 10)

Only respond with the appropriate action based on the user's intent and fill in as many parameters as possible. Do not make assumptions. Ask when uncertain.

User input: {user_input}
"""

    async def process_voice_command(
        self, user_input: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process voice command and return structured response

        Args:
            user_input: User's speech-to-text content
            conversation_id: Conversation ID, auto-generated if not provided

        Returns:
            Structured response dictionary
        """
        try:
            # Generate conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            # In test environment, return mock response
            if settings.environment == "test":
                logger.info(f"Test mode: Mock LLM response for input: {user_input}")
                return {
                    "conversationId": conversation_id,
                    "intentId": "CREATE_TASK",
                    "status": "confirmed",
                    "parameters": {
                        "title": "Test task",
                        "description": "This is a test task created in test mode",
                    },
                    "message": "Test task created successfully",
                }

            # Build complete prompt
            full_prompt = self.base_prompt.format(user_input=user_input)

            # Call Gemini API
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": settings.vertex_ai_max_tokens,
                    "temperature": settings.vertex_ai_temperature,
                },
            )

            # Parse response
            response_text = response.text.strip()
            logger.info(f"LLM response: {response_text}")

            # Try to parse JSON
            try:
                result = json.loads(response_text)

                # Ensure required fields exist
                if "conversationId" not in result:
                    result["conversationId"] = conversation_id

                return result

            except json.JSONDecodeError:
                logger.error(f"Cannot parse LLM response as JSON: {response_text}")
                return {
                    "conversationId": conversation_id,
                    "intentId": "UNKNOWN",
                    "status": "unknown",
                    "parameters": {},
                    "message": "Sorry, I cannot understand your command. Please try again.",
                }

        except Exception as e:
            logger.error(f"LLM processing failed: {str(e)}")
            return {
                "conversationId": conversation_id or str(uuid.uuid4()),
                "intentId": "UNKNOWN",
                "status": "unknown",
                "parameters": {},
                "message": "An error occurred while processing your command. Please try again later.",
            }

    def extract_task_parameters(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract task parameters from LLM response

        Args:
            llm_response: LLM response dictionary

        Returns:
            Task parameters dictionary
        """
        intent_id = llm_response.get("intentId", "UNKNOWN")
        parameters = llm_response.get("parameters", {})

        # Process parameters based on different intents
        if intent_id == "CREATE_TASK":
            return {
                "action": "create",
                "title": parameters.get("title"),
                "description": parameters.get("description"),
                "due_date": parameters.get("due_date"),
                "priority": parameters.get("priority", "medium"),
            }
        elif intent_id == "DELETE_TASK":
            return {
                "action": "delete",
                "task_id": parameters.get("task_id"),
                "title": parameters.get("title"),
            }
        elif intent_id == "UPDATE_TASK":
            return {
                "action": "update",
                "task_id": parameters.get("task_id"),
                "title": parameters.get("title"),
                "description": parameters.get("description"),
                "due_date": parameters.get("due_date"),
                "priority": parameters.get("priority"),
                "status": parameters.get("status"),
            }
        elif intent_id == "COMPLETE_TASK":
            return {
                "action": "complete",
                "task_id": parameters.get("task_id"),
                "title": parameters.get("title"),
            }
        elif intent_id == "QUERY_TASKS":
            return {
                "action": "query",
                "status": parameters.get("status"),
                "priority": parameters.get("priority"),
                "limit": parameters.get("limit", 10),
            }
        else:
            return {
                "action": "unknown",
                "message": llm_response.get("message", "Cannot understand command"),
            }


# Create global instance
llm_service = LLMService()
