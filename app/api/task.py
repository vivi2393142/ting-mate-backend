from fastapi import Depends, HTTPException, Path

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import delete_route, get_route, post_route, put_route
from app.repositories.activity_log import ActivityLogRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.schemas.task import (
    CreateTaskRequest,
    TaskListResponse,
    TaskResponse,
    UpdateTaskFields,
    UpdateTaskStatusRequest,
)
from app.schemas.user import User
from app.services.notification_manager import NotificationManager
from app.services.task import (
    delete_task,
    get_tasks_for_user,
    update_task,
    update_task_status,
)
from app.utils.user import get_actual_linked_carereceiver_id


@get_route(
    path="/tasks",
    summary="Get Tasks",
    description="Get all tasks for the current user.",
    response_model=TaskListResponse,
    tags=["task"],
)
def get_tasks(user: User = Depends(get_current_user_or_create_anonymous)):
    tasks = get_tasks_for_user(user.id, user.role)
    return TaskListResponse(tasks=tasks)


@post_route(
    path="/tasks",
    summary="Create Task",
    description="Create a new task for the current user.",
    response_model=TaskResponse,
    tags=["task"],
)
def create_task(
    user: User = Depends(get_current_user_or_create_anonymous),
    req: CreateTaskRequest = None,
):
    # Get actual task owner ID
    actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
    if not actual_owner_id:
        raise HTTPException(
            status_code=400, detail="No linked carereceiver found for caregiver"
        )

    task = TaskRepository.create_task(actual_owner_id, req, user.id)

    # Log the task creation
    reminder_time = f"{req.reminder_time.hour:02d}:{req.reminder_time.minute:02d}"
    ActivityLogRepository.log_task_create(
        user_id=user.id,
        target_user_id=actual_owner_id,
        task_title=req.title,
        reminder_time=reminder_time,
    )

    # Add notification
    group_user_ids = UserRepository.get_group_user_ids(user.id)
    for user_in_group in group_user_ids:
        if user_in_group != user.id:
            NotificationManager.notify_task_created(
                user_id=user_in_group,
                executor_user_id=user.id,
                task_id=task.id,
            )

    return TaskResponse(task=task)


@get_route(
    path="/tasks/{task_id}",
    summary="Get Task by ID",
    description="Get a specific task by its ID.",
    response_model=TaskResponse,
    tags=["task"],
)
def get_task(
    user: User = Depends(get_current_user_or_create_anonymous), task_id: str = Path(...)
):
    # Get actual task owner ID
    actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
    if not actual_owner_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(task=task)


@put_route(
    path="/tasks/{task_id}",
    summary="Update Task",
    description="Update a task's fields by its ID.",
    response_model=TaskResponse,
    tags=["task"],
)
def update_task_api(
    user: User = Depends(get_current_user_or_create_anonymous),
    task_id: str = Path(...),
    updates: UpdateTaskFields = None,
):
    # Get the task before updating for logging
    actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
    if not actual_owner_id:
        raise HTTPException(status_code=404, detail="Task not found")

    original_task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task = update_task(user.id, user.role, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

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
            task_title=task.title,
            updated_fields=updated_fields,
        )

    # Add notification for task update
    group_user_ids = UserRepository.get_group_user_ids(user.id)
    for user_in_group in group_user_ids:
        if user_in_group != user.id:
            NotificationManager.notify_task_updated(
                user_id=user_in_group,
                executor_user_id=user.id,
                task_id=task.id,
            )

    return TaskResponse(task=task)


@put_route(
    path="/tasks/{task_id}/status",
    summary="Update Task Status",
    description="Update the completion status of a task by its ID.",
    response_model=TaskResponse,
    tags=["task"],
)
def update_task_status_api(
    user: User = Depends(get_current_user_or_create_anonymous),
    task_id: str = Path(...),
    status: UpdateTaskStatusRequest = None,
):
    # Get the task before updating for logging
    actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
    if not actual_owner_id:
        raise HTTPException(status_code=404, detail="Task not found")

    original_task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")

    task = update_task_status(user.id, user.role, task_id, status.completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Log the task status update
    ActivityLogRepository.log_task_status_update(
        user_id=user.id,
        target_user_id=actual_owner_id,
        task_title=task.title,
        completed=status.completed,
    )

    # Add notification for task completed
    if status.completed is True:
        group_user_ids = UserRepository.get_group_user_ids(user.id)
        for user_in_group in group_user_ids:
            if user_in_group != user.id:
                NotificationManager.notify_task_completed(
                    user_id=user_in_group,
                    executor_user_id=user.id,
                    task_id=task.id,
                )

    return TaskResponse(task=task)


@delete_route(
    path="/tasks/{task_id}",
    summary="Delete Task",
    description="Delete a task by its ID.",
    tags=["task"],
)
def delete_task_api(
    user: User = Depends(get_current_user_or_create_anonymous),
    task_id: str = Path(...),
):
    # Get the task before deleting for logging
    actual_owner_id = get_actual_linked_carereceiver_id(user.id, user.role)
    if not actual_owner_id:
        raise HTTPException(status_code=404, detail="Task not found")

    original_task = TaskRepository.get_task_by_id(actual_owner_id, task_id)
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")

    success = delete_task(user.id, user.role, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    # Log the task deletion
    ActivityLogRepository.log_task_delete(
        user_id=user.id, target_user_id=actual_owner_id, task_title=original_task.title
    )

    # Add notification for task deleted
    group_user_ids = UserRepository.get_group_user_ids(user.id)
    for user_in_group in group_user_ids:
        if user_in_group != user.id:
            NotificationManager.notify_task_deleted(
                user_id=user_in_group,
                executor_user_id=user.id,
                task_id=task_id,
            )

    return {"message": "Task deleted successfully"}
