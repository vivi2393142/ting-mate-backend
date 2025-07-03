from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_current_user_or_anonymous
from app.schemas.task import Task, UpdateTaskFields, UpdateTaskStatusRequest
from app.services.task import (
    add_task,
    get_tasks_for_user,
    update_task,
    update_task_status,
)

router = APIRouter()


@router.get("/tasks", response_model=List[Task])
def get_tasks(user=Depends(get_current_user_or_anonymous)):
    return get_tasks_for_user(user.id)


@router.post("/tasks", response_model=Task)
def create_task(user=Depends(get_current_user_or_anonymous), task: Task = None):
    add_task(user.id, task)
    return task


@router.get("/tasks/{task_id}", response_model=Task)
def get_task(user=Depends(get_current_user_or_anonymous), task_id: str = Path(...)):
    tasks = get_tasks_for_user(user.id)
    for t in tasks:
        if t.id == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")


@router.put("/tasks/{task_id}", response_model=Task)
def update_task_api(
    user=Depends(get_current_user_or_anonymous),
    task_id: str = Path(...),
    updates: UpdateTaskFields = None,
):
    task = update_task(user.id, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/tasks/{task_id}", response_model=Task)
def update_task_status_api(
    user=Depends(get_current_user_or_anonymous),
    task_id: str = Path(...),
    status: UpdateTaskStatusRequest = None,
):
    task = update_task_status(user.id, task_id, status.completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
