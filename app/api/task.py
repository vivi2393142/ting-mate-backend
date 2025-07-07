from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_current_user_or_anonymous
from app.core.api_decorator import get_route, post_route, put_route
from app.repositories.task import TaskRepository
from app.schemas.task import (
    CreateTaskRequest,
    TaskListResponse,
    TaskResponse,
    UpdateTaskFields,
    UpdateTaskStatusRequest,
)
from app.services.task import get_tasks_for_user, update_task, update_task_status

router = APIRouter()


@get_route(
    path="/tasks",
    summary="Get Tasks",
    description="Get all tasks for the current user.",
    response_model=TaskListResponse,
    tags=["task"],
)
def get_tasks(user=Depends(get_current_user_or_anonymous)):
    tasks = get_tasks_for_user(user.id)
    return TaskListResponse(tasks=tasks)


@post_route(
    path="/tasks",
    summary="Create Task",
    description="Create a new task for the current user.",
    response_model=TaskResponse,
    tags=["task"],
)
def create_task(
    user=Depends(get_current_user_or_anonymous), req: CreateTaskRequest = None
):
    task = TaskRepository.create_task(user.id, req)
    return TaskResponse(task=task)


@get_route(
    path="/tasks/{task_id}",
    summary="Get Task by ID",
    description="Get a specific task by its ID.",
    response_model=TaskResponse,
    tags=["task"],
)
def get_task(user=Depends(get_current_user_or_anonymous), task_id: str = Path(...)):
    task = TaskRepository.get_task_by_id(user.id, task_id)
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
    user=Depends(get_current_user_or_anonymous),
    task_id: str = Path(...),
    updates: UpdateTaskFields = None,
):
    task = update_task(user.id, task_id, updates)
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
    user=Depends(get_current_user_or_anonymous),
    task_id: str = Path(...),
    status: UpdateTaskStatusRequest = None,
):
    task = update_task_status(user.id, task_id, status.completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(task=task)
