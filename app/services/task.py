from typing import List, Optional

from app.repositories.task import TaskRepository
from app.schemas.task import Task, TaskDB, UpdateTaskFields


def taskdb_to_task(task: TaskDB) -> Task:
    return Task(**task.model_dump(exclude={"deleted"}))


def get_tasks_for_user(user_id: str) -> List[Task]:
    """Get all tasks for a user from database"""
    return TaskRepository.get_tasks_for_user(user_id)


def add_task(user_id: str, task: TaskDB):
    """Add a new task to database"""
    TaskRepository.create_task(user_id, task)


def update_task(
    user_id: str, task_id: str, updates: UpdateTaskFields
) -> Optional[Task]:
    """Update a task in database"""
    return TaskRepository.update_task(user_id, task_id, updates)


def update_task_status(user_id: str, task_id: str, completed: bool) -> Optional[Task]:
    """Update task completion status in database"""
    return TaskRepository.update_task_status(user_id, task_id, completed)


def delete_task(user_id: str, task_id: str) -> bool:
    """Soft delete a task from database"""
    return TaskRepository.delete_task(user_id, task_id)
