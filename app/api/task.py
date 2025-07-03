from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_current_user_or_anonymous
from app.core.api_decorator import get_route, post_route, put_route
from app.schemas.task import (
    CreateTaskRequest,
    Task,
    UpdateTaskFields,
    UpdateTaskStatusRequest,
)
from app.services.task import (
    add_task,
    get_tasks_for_user,
    taskdb_to_task,
    update_task,
    update_task_status,
)

router = APIRouter()


@get_route(
    path="/tasks",
    summary="Get Tasks",
    description="Get all tasks for the current user.",
    response_model=List[Task],
    tags=["task"],
)
def get_tasks(user=Depends(get_current_user_or_anonymous)):
    return get_tasks_for_user(user.id)


@post_route(
    path="/tasks",
    summary="Create Task",
    description="Create a new task for the current user.",
    response_model=Task,
    tags=["task"],
)
def create_task(
    user=Depends(get_current_user_or_anonymous), req: CreateTaskRequest = None
):
    from app.schemas.task import TaskDB

    now = datetime.now()
    task_db = TaskDB(
        id=str(uuid4()),
        title=req.title,
        icon=req.icon,
        reminderTime=req.reminderTime,
        recurrence=req.recurrence,
        completed=False,
        createdAt=now,
        updatedAt=now,
        completedAt=None,
        completedBy=None,
        deleted=False,
    )
    add_task(user.id, task_db)
    return taskdb_to_task(task_db)


@get_route(
    path="/tasks/{task_id}",
    summary="Get Task by ID",
    description="Get a specific task by its ID.",
    response_model=Task,
    tags=["task"],
)
def get_task(user=Depends(get_current_user_or_anonymous), task_id: str = Path(...)):
    tasks = get_tasks_for_user(user.id)
    for t in tasks:
        if t.id == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")


@put_route(
    path="/tasks/{task_id}",
    summary="Update Task",
    description="Update a task's fields by its ID.",
    response_model=Task,
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
    return task


@put_route(
    path="/tasks/{task_id}/status",
    summary="Update Task Status",
    description="Update the completion status of a task by its ID.",
    response_model=Task,
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
    return task
