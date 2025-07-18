import json
import logging
import os
from typing import Optional

from fastapi import Body, Depends, File, Form, HTTPException, UploadFile, status
from nanoid import generate

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import post_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.assistant_conversation import AssistantConversationRepository
from app.repositories.assistant_pending_task import AssistantPendingTaskRepository
from app.repositories.task import TaskRepository
from app.schemas.assistant_conversation import (
    AssistantConversationCreate,
    AssistantConversationUpdate,
)
from app.schemas.assistant_pending_task import AssistantPendingTaskCreate
from app.schemas.assistant_pending_task import IntentType as PendingIntentType
from app.schemas.task import (
    CreateTaskRequest,
    RecurrenceRule,
    RecurrenceUnit,
    ReminderTime,
    UpdateTaskFields,
)
from app.schemas.user import Role, User
from app.services.llm import IntentType, Status, llm_service
from app.services.notification_manager import NotificationManager
from app.services.speech import speech_service
from app.services.task import get_tasks_for_user
from app.utils.user import get_actual_linked_carereceiver_id

logger = logging.getLogger(__name__)

# Maximum number of turns per conversation to prevent infinite loops
MAX_CONVERSATION_TURNS = 5


def _get_active_tasks(user_id: str, user_role: Role = None) -> list:
    """Get all active (non-deleted) tasks for the user"""
    db_tasks = get_tasks_for_user(user_id, user_role)
    return [{"task_id": t.id, "title": t.title} for t in db_tasks]


def _get_previous_candidates(
    active_tasks: list, previous_result: Optional[dict]
) -> list:
    """Get task candidates from previous_result's task_candidate_id_list"""
    if not previous_result:
        return active_tasks

    candidate_ids = previous_result.get("task_candidate_id_list", [])
    if not candidate_ids:
        return active_tasks

    return [task for task in active_tasks if task["task_id"] in candidate_ids]


def _get_filtered_candidates(
    active_tasks: list, previous_result: Optional[dict]
) -> list:
    """Get filtered candidates for delete/query tasks based on previous result"""
    if not previous_result:
        return active_tasks

    return _get_previous_candidates(active_tasks, previous_result)


def _generate_confirmation_message(
    intent_type: IntentType, task_data: dict, user: User = None
) -> str:
    """Generate confirmation message based on intent type and task data"""
    if intent_type == IntentType.CREATE_TASK:
        title = task_data.get("title", "Unknown task")
        hour = task_data.get("reminder_hour", 0)
        minute = task_data.get("reminder_minute", 0)
        time_str = f"{hour:02d}:{minute:02d}"
        return f"Okay! Should I create the task '{title}' and remind you at {time_str}?"

    elif intent_type == IntentType.UPDATE_TASK:
        updates = []
        if "title" in task_data:
            updates.append(f"title to '{task_data['title']}'")
        if "reminder_hour" in task_data or "reminder_minute" in task_data:
            hour = task_data.get("reminder_hour", 0)
            minute = task_data.get("reminder_minute", 0)
            updates.append(f"reminder time to {hour:02d}:{minute:02d}")
        if "completed" in task_data:
            status = "completed" if task_data["completed"] else "uncompleted"
            updates.append(f"status to {status}")
        update_str = ", ".join(updates)
        if update_str:
            return f"Got it. Do you want me to update this task to {update_str}?"
        else:
            return "Got it. Do you want me to update this task?"

    elif intent_type == IntentType.DELETE_TASK:
        # Try to get user_id and task_id from task_data
        user_id = task_data.get("user_id")
        task_id = task_data.get("result")
        if user_id and task_id and user:
            # Get actual task owner ID for caregiver
            actual_owner_id = get_actual_linked_carereceiver_id(user_id, user.role)
            if actual_owner_id:
                task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
                if task:
                    title = getattr(task, "title", "Unknown task")
                    reminder_time = getattr(task, "reminder_time", None)
                    if reminder_time:
                        time_str = (
                            f"{reminder_time.hour:02d}:{reminder_time.minute:02d}"
                        )
                        return f"Alright. Should I go ahead and delete the task '{title}' at {time_str}?"
                    else:
                        return (
                            f"Alright. Should I go ahead and delete the task '{title}'?"
                        )
        # fallback
        return "Alright. Should I go ahead and delete this task?"

    return "Want me to go ahead with that?"


@post_route(
    path="/assistant/text-command",
    summary="Text-based assistant command endpoint",
    description=(
        "Unified endpoint for LLM-driven assistant flow with text input. "
        "Handles intent detection, slot filling, and multi-turn disambiguation."
    ),
    tags=["assistant"],
)
async def text_command(
    user: User = Depends(get_current_user_or_create_anonymous),
    user_input: str = Body(..., description="User input text"),
    conversation_id: Optional[str] = Body(
        None, description="Conversation/session id for multi-turn context"
    ),
):
    # Generate conversation_id if not provided
    if not conversation_id:
        conversation_id = generate()

    # Get assistant conversation from database
    assistant_conversation = AssistantConversationRepository.get_conversation(
        conversation_id
    )

    # Check conversation turn limit
    if (
        assistant_conversation
        and assistant_conversation.turn_count >= MAX_CONVERSATION_TURNS
    ):
        return {
            "conversation_id": conversation_id,
            "status": Status.FAILED,
            "further_question": "I'm sorry, this conversation has reached its limit. "
            "Please start a new conversation if you need help.",
        }

    logger.info("=== Check Prev Conv State ===")
    # Determine intent_type and previous_response
    if assistant_conversation:
        intent_type = (
            IntentType(assistant_conversation.intent_type)
            if assistant_conversation.intent_type
            else None
        )
        prev_resp = (
            json.dumps(assistant_conversation.llm_result)
            if assistant_conversation.llm_result
            else None
        )
        logger.info(f"Get Prev Conversation type: {intent_type}")
        logger.info(
            f"Get Prev Conversation result: {assistant_conversation.llm_result}"
        )
        logger.info(f"Get Prev Conversation result(JSON): {prev_resp}")
    else:
        intent_type = await llm_service.detect_intent(
            user_input=user_input, user_id=user.id, conversation_id=conversation_id
        )
        prev_resp = None
        logger.info(f"Get New Conversation type: {intent_type}")
    logger.info("=== Check Intent Type ===")
    if intent_type == IntentType.DELETE_TASK:
        active_tasks = _get_active_tasks(user.id, user.role)
        task_candidates = _get_filtered_candidates(
            active_tasks,
            assistant_conversation.llm_result if assistant_conversation else None,
        )

        llm_resp = await llm_service.extract_delete_task(
            task_candidates=json.dumps(task_candidates),
            user_input=user_input,
            previous_response=prev_resp,
            user_id=user.id,
            conversation_id=conversation_id,
        )
    elif intent_type == IntentType.UPDATE_TASK:
        active_tasks = _get_active_tasks(user.id, user.role)

        llm_resp = await llm_service.extract_update_task(
            active_tasks=json.dumps(active_tasks),
            user_input=user_input,
            previous_response=prev_resp,
            user_id=user.id,
            conversation_id=conversation_id,
        )
    elif intent_type == IntentType.CREATE_TASK:
        llm_resp = await llm_service.extract_create_task(
            user_input=user_input,
            previous_response=prev_resp,
            user_id=user.id,
            conversation_id=conversation_id,
        )
    else:
        return {
            "conversation_id": conversation_id,
            "status": Status.FAILED,
            "further_question": "I'm sorry, I don't know how to help you with that. "
            "Please start a new conversation if you need help.",
        }

    # If status is CONFIRMED, create pending task and return confirmation message
    if llm_resp.status == Status.CONFIRMED:
        # Prepare task data based on intent type
        task_data = {}
        if intent_type == IntentType.CREATE_TASK:
            result = llm_resp.result
            task_data = {
                "title": result.title,
                "reminder_hour": result.reminder_hour,
                "reminder_minute": result.reminder_minute,
                "recurrence_interval": result.recurrence_interval,
                "recurrence_unit": (
                    result.recurrence_unit.value if result.recurrence_unit else None
                ),
                "recurrence_days_of_week": result.recurrence_days_of_week,
                "recurrence_days_of_month": result.recurrence_days_of_month,
            }
        elif intent_type == IntentType.UPDATE_TASK:
            result = llm_resp.result
            task_data = {
                "task_id": result.task_id,
                "title": result.title,
                "reminder_hour": result.reminder_hour,
                "reminder_minute": result.reminder_minute,
                "recurrence_interval": result.recurrence_interval,
                "recurrence_unit": (
                    result.recurrence_unit.value if result.recurrence_unit else None
                ),
                "recurrence_days_of_week": result.recurrence_days_of_week,
                "recurrence_days_of_month": result.recurrence_days_of_month,
            }
        elif intent_type == IntentType.DELETE_TASK:
            task_data = {
                "result": llm_resp.result,
                "user_id": user.id,
            }

        # Create pending task
        pending_task = AssistantPendingTaskCreate(
            conversation_id=conversation_id,
            user_id=user.id,
            intent_type=PendingIntentType(intent_type.value),
            task_data=task_data,
        )

        AssistantPendingTaskRepository.create_pending_task(pending_task)

        # Generate confirmation message
        confirmation_message = _generate_confirmation_message(
            intent_type, task_data, user
        )

        return {
            "conversation_id": conversation_id,
            "status": Status.CONFIRMED,
            "further_question": confirmation_message,
        }

    # Store LLM result and intent_type in database
    current_turn_count = (
        assistant_conversation.turn_count + 1 if assistant_conversation else 1
    )

    if assistant_conversation:
        # Update existing assistant conversation
        updates = AssistantConversationUpdate(
            intent_type=intent_type.value,
            llm_result=(
                llm_resp.model_dump() if hasattr(llm_resp, "model_dump") else llm_resp
            ),
            turn_count=current_turn_count,
        )
        AssistantConversationRepository.update_conversation(conversation_id, updates)
    else:
        # Create new conversation state
        new_state = AssistantConversationCreate(
            conversation_id=conversation_id,
            user_id=user.id,
            intent_type=intent_type.value,
            llm_result=(
                llm_resp.model_dump() if hasattr(llm_resp, "model_dump") else llm_resp
            ),
            turn_count=current_turn_count,
        )
        AssistantConversationRepository.create_conversation(new_state)

    # Only return minimal info to frontend
    return {
        "conversation_id": conversation_id,
        "status": llm_resp.status,
        "further_question": getattr(llm_resp, "further_question", None),
    }


@post_route(
    path="/assistant/execute-pending-task",
    summary="Execute pending task endpoint",
    description="Execute a pending task after user confirmation",
    tags=["assistant"],
)
async def execute_pending_task(
    user: User = Depends(get_current_user_or_create_anonymous),
    conversation_id: str = Body(..., description="Conversation ID of the pending task"),
):
    try:
        # Get pending task
        pending_task = (
            AssistantPendingTaskRepository.get_pending_task_by_conversation_id(
                conversation_id
            )
        )

        if not pending_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending task not found or expired",
            )

        if pending_task.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to execute this pending task",
            )

        task_data = pending_task.task_data
        result = None

        # Execute the pending task based on intent type
        if pending_task.intent_type == PendingIntentType.CREATE_TASK:
            # Create task
            create_request = CreateTaskRequest(
                title=task_data["title"],
                icon="📝",  # TODO:Default icon, use LLM to generate icon
                reminder_time=ReminderTime(
                    hour=task_data["reminder_hour"], minute=task_data["reminder_minute"]
                ),
                recurrence=(
                    RecurrenceRule(
                        interval=task_data["recurrence_interval"],
                        unit=RecurrenceUnit(task_data["recurrence_unit"]),
                        days_of_week=task_data["recurrence_days_of_week"],
                        days_of_month=task_data["recurrence_days_of_month"],
                    )
                    if task_data.get("recurrence_interval")
                    and task_data.get("recurrence_unit")
                    else None
                ),
            )

            # Get actual task owner ID for caregiver
            actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
            if not actual_owner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No linked carereceiver found for caregiver",
                )

            result = TaskRepository.create_task(
                actual_owner_id, create_request, user.id
            )

            # Log the task creation
            reminder_time = f"{create_request.reminder_time.hour:02d}:{create_request.reminder_time.minute:02d}"
            ActivityLogRepository.log_task_create(
                user_id=user.id,
                target_user_id=actual_owner_id,
                task_title=create_request.title,
                reminder_time=reminder_time,
            )

            # Add notification
            NotificationManager.notify_task_created(
                user_id=actual_owner_id, linked_user_id=user.id, task_id=result.id
            )

        elif pending_task.intent_type == PendingIntentType.UPDATE_TASK:
            # Update task
            updates = UpdateTaskFields()
            if "title" in task_data and task_data["title"]:
                updates.title = task_data["title"]
            if "reminder_hour" in task_data or "reminder_minute" in task_data:
                updates.reminder_time = ReminderTime(
                    hour=task_data.get("reminder_hour", 0),
                    minute=task_data.get("reminder_minute", 0),
                )
            if (
                "recurrence_interval" in task_data
                and "recurrence_unit" in task_data
                and "recurrence_days_of_week" in task_data
                and "recurrence_days_of_month" in task_data
            ):
                updates.recurrence = RecurrenceRule(
                    interval=task_data["recurrence_interval"],
                    unit=RecurrenceUnit(task_data["recurrence_unit"]),
                    days_of_week=task_data["recurrence_days_of_week"],
                    days_of_month=task_data["recurrence_days_of_month"],
                )
            if "completed" in task_data:
                updates.completed = task_data["completed"]

            # Get actual task owner ID for caregiver
            actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
            if not actual_owner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No linked carereceiver found for caregiver",
                )

            result = TaskRepository.update_task(
                actual_owner_id, task_data["task_id"], updates
            )

            # Log the task update
            updated_fields = {}
            if updates.title is not None:
                updated_fields["title"] = updates.title
            if updates.reminder_time is not None:
                updated_fields["reminder_time"] = (
                    f"{updates.reminder_time.hour:02d}:{updates.reminder_time.minute:02d}"
                )
            if updates.recurrence is not None:
                updated_fields["recurrence"] = (
                    f"{updates.recurrence.interval} {updates.recurrence.unit}"
                )

            if updated_fields:
                ActivityLogRepository.log_task_update(
                    user_id=user.id,
                    target_user_id=actual_owner_id,
                    task_title=result.title,
                    updated_fields=updated_fields,
                )

        elif pending_task.intent_type == PendingIntentType.DELETE_TASK:
            # Delete task
            # Get actual task owner ID for caregiver
            actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
            if not actual_owner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No linked carereceiver found for caregiver",
                )

            task_id = task_data["result"]
            success = TaskRepository.delete_task(actual_owner_id, task_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found or already deleted",
                )
            result = {"deleted": True}

            task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
            if task:
                title = getattr(task, "title", "Unknown task")

            # Log the task deletion
            ActivityLogRepository.log_task_delete(
                user_id=user.id,
                target_user_id=actual_owner_id,
                task_title=title if title else "Unknown task",
            )

        # Delete the pending task after successful execution
        AssistantPendingTaskRepository.delete_pending_task(pending_task.id)

        return {
            "success": True,
            "message": "Task executed successfully",
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing pending task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute pending task",
        )


@post_route(
    path="/assistant/voice-command",
    summary="Voice-based assistant command endpoint",
    description=(
        "Unified endpoint for LLM-driven assistant flow with voice input. "
        "Handles speech-to-text conversion, intent detection, slot filling, and multi-turn disambiguation."
    ),
    tags=["assistant"],
)
async def voice_command(
    user: User = Depends(get_current_user_or_create_anonymous),
    audio_file: UploadFile = File(..., description="Audio file"),
    conversation_id: Optional[str] = Body(
        None, description="Conversation/session id for multi-turn context"
    ),
    encoding: Optional[str] = Form(
        None, description="Audio encoding format (optional)"
    ),
) -> dict:
    try:
        audio_content = await audio_file.read()
        ext = (
            os.path.splitext(audio_file.filename)[-1].replace(".", "").lower()
            if audio_file.filename
            else None
        )
        transcript = speech_service.transcribe_audio_content(
            audio_content, file_format=ext
        )
        if not transcript:
            raise HTTPException(
                status_code=400, detail="Speech-to-text failed or no speech detected."
            )

        # Call text_command to handle the transcript
        result = await text_command(
            user=user,
            user_input=transcript,
            conversation_id=conversation_id,
        )
        # Map the result to a standard response structure
        data = {
            "conversation_id": None,
            "status": None,
            "further_question": None,
            "user_input": transcript,
        }
        if result.data:
            data["conversation_id"] = result.data["conversation_id"]
            data["status"] = result.data["status"]
            data["further_question"] = result.data["further_question"]
        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in voice command: {str(e)}")
