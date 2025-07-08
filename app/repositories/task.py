"""
Task repository - handles all database operations for tasks
"""

import json
from datetime import datetime
from typing import List, Optional

from nanoid import generate

from app.core.database import execute_query, execute_update
from app.schemas.task import CreateTaskRequest, Task, TaskDB, UpdateTaskFields


class TaskRepository:
    """Repository for task data access operations"""

    @staticmethod
    def create_task(user_id: str, task_create: CreateTaskRequest) -> Task:
        """Create a new task in database"""
        try:
            # Generate nanoid for new task
            task_id = generate()
            now = datetime.now()

            # Prepare recurrence data
            recurrence_interval = None
            recurrence_unit = None
            recurrence_days_of_week = None
            recurrence_days_of_month = None

            if task_create.recurrence:
                recurrence_interval = task_create.recurrence.interval
                recurrence_unit = task_create.recurrence.unit.value
                recurrence_days_of_week = (
                    json.dumps(task_create.recurrence.days_of_week)
                    if task_create.recurrence.days_of_week
                    else None
                )
                recurrence_days_of_month = (
                    json.dumps(task_create.recurrence.days_of_month)
                    if task_create.recurrence.days_of_month
                    else None
                )

            # Insert task into database
            insert_sql = """
            INSERT INTO tasks (
                id, user_id, title, icon, reminder_hour, reminder_minute,
                recurrence_interval, recurrence_unit, 
                recurrence_days_of_week, recurrence_days_of_month,
                completed, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_update(
                insert_sql,
                (
                    task_id,
                    user_id,
                    task_create.title,
                    task_create.icon,
                    task_create.reminder_time.hour,
                    task_create.reminder_time.minute,
                    recurrence_interval,
                    recurrence_unit,
                    recurrence_days_of_week,
                    recurrence_days_of_month,
                    False,
                    user_id,
                    user_id,
                ),
            )

            # Return task object
            return Task(
                id=task_id,
                title=task_create.title,
                icon=task_create.icon,
                reminder_time=task_create.reminder_time,
                recurrence=task_create.recurrence,
                completed=False,
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
                completed_at=None,
                completed_by=None,
            )

        except Exception as e:
            raise ValueError(f"Failed to create task: {str(e)}")

    @staticmethod
    def get_tasks_for_user(user_id: str) -> List[Task]:
        """Get all non-deleted tasks for a user"""
        try:
            query = """
            SELECT * FROM tasks
            WHERE user_id = %s AND deleted = FALSE
            ORDER BY created_at DESC
            """

            results = execute_query(query, (user_id,))
            tasks = []

            for result in results:
                task = TaskRepository._row_to_task(result)
                if task:
                    tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error getting tasks for user: {e}")
            return []

    @staticmethod
    def get_task_by_id(user_id: str, task_id: str) -> Optional[Task]:
        """Get a specific task by ID for a user"""
        try:
            query = """
            SELECT * FROM tasks
            WHERE id = %s AND user_id = %s AND deleted = FALSE
            """

            result = execute_query(query, (task_id, user_id))

            if result:
                return TaskRepository._row_to_task(result[0])

            return None

        except Exception as e:
            print(f"Error getting task by id: {e}")
            return None

    @staticmethod
    def update_task(
        user_id: str, task_id: str, updates: UpdateTaskFields
    ) -> Optional[Task]:
        """Update a task's fields"""
        try:
            # First check if task exists and belongs to user
            task = TaskRepository.get_task_by_id(user_id, task_id)
            if not task:
                return None

            # Build update query dynamically
            update_fields = []
            update_values = []

            if updates.title is not None:
                update_fields.append("title = %s")
                update_values.append(updates.title)

            if updates.icon is not None:
                update_fields.append("icon = %s")
                update_values.append(updates.icon)

            if updates.reminder_time is not None:
                update_fields.append("reminder_hour = %s")
                update_fields.append("reminder_minute = %s")
                update_values.extend(
                    [updates.reminder_time.hour, updates.reminder_time.minute]
                )

            if updates.recurrence is not None:
                if updates.recurrence:
                    update_fields.append("recurrence_interval = %s")
                    update_fields.append("recurrence_unit = %s")
                    update_fields.append("recurrence_days_of_week = %s")
                    update_fields.append("recurrence_days_of_month = %s")
                    update_values.extend(
                        [
                            updates.recurrence.interval,
                            updates.recurrence.unit.value,
                            (
                                json.dumps(updates.recurrence.days_of_week)
                                if updates.recurrence.days_of_week
                                else None
                            ),
                            (
                                json.dumps(updates.recurrence.days_of_month)
                                if updates.recurrence.days_of_month
                                else None
                            ),
                        ]
                    )
                else:
                    update_fields.append("recurrence_interval = NULL")
                    update_fields.append("recurrence_unit = NULL")
                    update_fields.append("recurrence_days_of_week = NULL")
                    update_fields.append("recurrence_days_of_month = NULL")

            if updates.completed is not None:
                update_fields.append("completed = %s")
                update_values.append(updates.completed)

            if not update_fields:
                return task  # No updates to make

            # Add updated_by and updated_at
            update_fields.append("updated_by = %s")
            update_values.append(user_id)

            update_sql = f"""
            UPDATE tasks
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s AND deleted = FALSE
            """

            update_values.extend([task_id, user_id])
            execute_update(update_sql, tuple(update_values))

            # Return updated task
            return TaskRepository.get_task_by_id(user_id, task_id)

        except Exception as e:
            print(f"Error updating task: {e}")
            return None

    @staticmethod
    def update_task_status(
        user_id: str, task_id: str, completed: bool
    ) -> Optional[Task]:
        """Update task completion status"""
        try:
            now = datetime.now()
            completed_at = now if completed else None
            completed_by = user_id if completed else None

            update_sql = """
            UPDATE tasks
            SET completed = %s, completed_at = %s, completed_by = %s, updated_by = %s
            WHERE id = %s AND user_id = %s AND deleted = FALSE
            """

            execute_update(
                update_sql,
                (completed, completed_at, completed_by, user_id, task_id, user_id),
            )

            return TaskRepository.get_task_by_id(user_id, task_id)

        except Exception as e:
            print(f"Error updating task status: {e}")
            return None

    @staticmethod
    def delete_task(user_id: str, task_id: str) -> bool:
        """Soft delete a task"""
        try:
            update_sql = """
            UPDATE tasks
            SET deleted = TRUE, updated_by = %s
            WHERE id = %s AND user_id = %s AND deleted = FALSE
            """

            result = execute_update(update_sql, (user_id, task_id, user_id))
            return result > 0

        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    @staticmethod
    def _row_to_task(row) -> Optional[Task]:
        """Convert database row to Task object"""
        try:
            from app.schemas.task import RecurrenceRule, RecurrenceUnit, ReminderTime

            # Parse recurrence data
            recurrence = None
            if row.get("recurrence_interval") and row.get("recurrence_unit"):
                days_of_week = None
                days_of_month = None

                if row.get("recurrence_days_of_week"):
                    days_of_week = json.loads(row["recurrence_days_of_week"])
                if row.get("recurrence_days_of_month"):
                    days_of_month = json.loads(row["recurrence_days_of_month"])

                recurrence = RecurrenceRule(
                    interval=row["recurrence_interval"],
                    unit=RecurrenceUnit(row["recurrence_unit"]),
                    days_of_week=days_of_week,
                    days_of_month=days_of_month,
                )

            return Task(
                id=row["id"],
                title=row["title"],
                icon=row["icon"],
                reminder_time=ReminderTime(
                    hour=row["reminder_hour"], minute=row["reminder_minute"]
                ),
                recurrence=recurrence,
                completed=row["completed"],
                created_at=row["created_at"],
                created_by=row["created_by"],
                updated_at=row["updated_at"],
                updated_by=row["updated_by"],
                completed_at=row.get("completed_at"),
                completed_by=row.get("completed_by"),
            )

        except Exception as e:
            print(f"Error converting row to task: {e}")
            return None

    @staticmethod
    def taskdb_to_task(taskdb: TaskDB) -> Task:
        """Convert TaskDB to Task"""
        return Task(
            id=taskdb.id,
            title=taskdb.title,
            icon=taskdb.icon,
            reminder_time=taskdb.reminder_time,
            recurrence=taskdb.recurrence,
            completed=taskdb.completed,
            created_at=taskdb.created_at,
            created_by=taskdb.created_by,
            updated_at=taskdb.updated_at,
            updated_by=taskdb.updated_by,
            completed_at=taskdb.completed_at,
            completed_by=taskdb.completed_by,
        )
