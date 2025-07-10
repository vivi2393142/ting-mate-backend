from typing import List, Optional

from app.repositories.task import TaskRepository
from app.schemas.task import Task, TaskDB, UpdateTaskFields
from app.schemas.user import Role
from app.services.link import LinkService


def taskdb_to_task(task: TaskDB) -> Task:
    return Task(**task.model_dump(exclude={"deleted"}))


def get_actual_task_owner_id(user_id: str, user_role: Role) -> str:
    """
    Get the actual task owner ID.
    - If user is CARERECEIVER: return user_id (own tasks)
    - If user is CAREGIVER: return linked carereceiver's ID (if exists)
    """
    if user_role == Role.CARERECEIVER:
        return user_id
    elif user_role == Role.CAREGIVER:
        # Get linked carereceivers
        linked_carereceivers = LinkService.get_caregiver_links(user_id)
        if linked_carereceivers:
            # Return the first linked carereceiver's ID
            return linked_carereceivers[0]["id"]
        else:
            # If no linked carereceiver, return None to indicate no tasks
            return None
    else:
        return user_id


def get_tasks_for_user(user_id: str, user_role: Role = None) -> List[Task]:
    """Get all tasks for a user from database, excluding overdue non-recurring tasks"""
    from datetime import datetime

    # Get actual task owner ID
    actual_owner_id = get_actual_task_owner_id(user_id, user_role)
    if not actual_owner_id:
        return []  # Caregiver with no linked carereceiver has no tasks

    all_tasks = TaskRepository.get_tasks_for_user(actual_owner_id)
    today = datetime.now().date()

    filtered_tasks = []
    for task in all_tasks:
        # Always include recurring tasks
        if task.recurrence is not None:
            filtered_tasks.append(task)
            continue
        # Only include non-recurring tasks if created today
        if hasattr(task, "created_at") and getattr(task, "created_at").date() == today:
            filtered_tasks.append(task)
    return filtered_tasks


def add_task(user_id: str, user_role: Role, task: TaskDB):
    """Add a new task to database"""
    actual_owner_id = get_actual_task_owner_id(user_id, user_role)
    if not actual_owner_id:
        raise ValueError("No linked carereceiver found for caregiver")
    TaskRepository.create_task(actual_owner_id, task, user_id)


def update_task(
    user_id: str, user_role: Role, task_id: str, updates: UpdateTaskFields
) -> Optional[Task]:
    """Update a task in database"""
    actual_owner_id = get_actual_task_owner_id(user_id, user_role)
    if not actual_owner_id:
        return None
    return TaskRepository.update_task(actual_owner_id, task_id, updates)


def update_task_status(
    user_id: str, user_role: Role, task_id: str, completed: bool
) -> Optional[Task]:
    """Update task completion status in database"""
    actual_owner_id = get_actual_task_owner_id(user_id, user_role)
    if not actual_owner_id:
        return None
    return TaskRepository.update_task_status(actual_owner_id, task_id, completed)


def delete_task(user_id: str, user_role: Role, task_id: str) -> bool:
    """Soft delete a task from database"""
    actual_owner_id = get_actual_task_owner_id(user_id, user_role)
    if not actual_owner_id:
        return False
    return TaskRepository.delete_task(actual_owner_id, task_id)
