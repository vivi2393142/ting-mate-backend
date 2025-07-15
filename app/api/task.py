from fastapi import Depends, HTTPException, Path

from app.api.deps import get_current_user_or_create_anonymous
from app.core.api_decorator import delete_route, get_route, post_route, put_route
from app.repositories.task import TaskRepository
from app.schemas.task import (
    CreateTaskRequest,
    TaskListResponse,
    TaskResponse,
    UpdateTaskFields,
    UpdateTaskStatusRequest,
)
from app.schemas.user import User
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
    task = update_task(user.id, user.role, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
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
    task = update_task_status(user.id, user.role, task_id, status.completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
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
    success = delete_task(user.id, user.role, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
