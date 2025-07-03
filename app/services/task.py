from typing import List, Optional

from app.db.fake_db import fake_tasks_db
from app.schemas.task import Task, TaskDB, UpdateTaskFields


def taskdb_to_response(task: TaskDB) -> Task:
    return Task(**task.model_dump(exclude={"deleted"}))


def get_tasks_for_user(user_id: str) -> List[Task]:
    # Only return tasks that are not deleted, and convert to Task
    return [
        taskdb_to_response(task)
        for task in fake_tasks_db.get(user_id, [])
        if not getattr(task, "deleted", False)
    ]


def add_task(user_id: str, task: TaskDB):
    if user_id not in fake_tasks_db:
        fake_tasks_db[user_id] = []
    fake_tasks_db[user_id].append(task)


def update_task(
    user_id: str, task_id: str, updates: UpdateTaskFields
) -> Optional[Task]:
    tasks = fake_tasks_db.get(user_id, [])
    for task in tasks:
        if task.id == task_id and not getattr(task, "deleted", False):
            update_data = updates.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(task, key, value)
            return taskdb_to_response(task)
    return None


def update_task_status(user_id: str, task_id: str, completed: bool) -> Optional[Task]:
    return update_task(user_id, task_id, UpdateTaskFields(completed=completed))


def delete_task(user_id: str, task_id: str) -> bool:
    tasks = fake_tasks_db.get(user_id, [])
    for task in tasks:
        if task.id == task_id:
            task.deleted = True
            return True
    return False
