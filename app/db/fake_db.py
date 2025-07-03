# TODO: replace with real database in the future

from app.schemas.task import RecurrenceRule, RecurrenceUnit, ReminderTime, TaskDB
from app.schemas.user import UserDB

# TODO: replace with real database

user1_id = "635acc4a-9dd4-44e1-b0f1-f86bd12b6e63"
user2_id = "b3157ca3-aa4d-4b7e-8a1f-972412be6b40"

fake_users_db = {
    # Registered user
    user1_id: UserDB(
        id=user1_id,
        email="user@example.com",
        hashed_password="$2b$12$7RSQMLM65WDMPFBezvITx.TOp4If6TrMNyvGscxBuwvu7bigFEsUK",  # noqa: E501
        anonymous_id=None,
    ),
    # Anonymous user
    user2_id: UserDB(
        id=user2_id,
        email=None,
        hashed_password=None,
        anonymous_id="anon_abc123",
    ),
}

# Fake tasks db: {user_id: [TaskDB, ...]}
fake_tasks_db = {
    user1_id: [
        TaskDB(
            id="task-1",
            title="Take medication",
            icon="💊",
            reminderTime=ReminderTime(hour=8, minute=0),
            recurrence=RecurrenceRule(interval=1, unit=RecurrenceUnit.DAY),
            completed=True,
            createdAt="2024-05-01T08:00:00Z",
            updatedAt="2024-05-01T08:10:00Z",
            completedAt="2024-05-01T08:15:00Z",
            completedBy=user1_id,
        ),
        TaskDB(
            id="task-2",
            title="Measure blood pressure & blood sugar",
            icon="🩺",
            recurrence=RecurrenceRule(interval=1, unit=RecurrenceUnit.DAY),
            reminderTime=ReminderTime(hour=9, minute=0),
            completed=True,
            completedAt="2024-05-03T09:15:00Z",
            createdAt="2024-05-03T09:00:00Z",
            updatedAt="2024-05-03T09:10:00Z",
            completedBy=user1_id,
        ),
        TaskDB(
            id="task-3",
            title="Walk",
            icon="🚶",
            recurrence=RecurrenceRule(
                interval=1, unit=RecurrenceUnit.WEEK, daysOfWeek=[1, 3, 5]
            ),
            reminderTime=ReminderTime(hour=16, minute=30),
            completed=False,
            createdAt="2024-04-20T16:30:00Z",
            updatedAt="2024-04-20T16:40:00Z",
        ),
        TaskDB(
            id="task-4",
            title="See doctor",
            icon="👨‍⚕️",
            recurrence=RecurrenceRule(
                interval=1, unit=RecurrenceUnit.MONTH, daysOfMonth=[15]
            ),
            reminderTime=ReminderTime(hour=10, minute=0),
            completed=False,
            createdAt="2024-04-01T10:00:00Z",
            updatedAt="2024-04-01T10:10:00Z",
        ),
        TaskDB(
            id="task-5",
            title="Drink water",
            icon="💧",
            recurrence=RecurrenceRule(interval=1, unit=RecurrenceUnit.DAY),
            reminderTime=ReminderTime(hour=10, minute=0),
            completed=False,
            createdAt="2024-05-10T10:00:00Z",
            updatedAt="2024-05-10T10:10:00Z",
        ),
        TaskDB(
            id="task-6",
            title="Exercise",
            icon="🏃‍♂️",
            recurrence=RecurrenceRule(interval=1, unit=RecurrenceUnit.DAY),
            reminderTime=ReminderTime(hour=19, minute=26),
            completed=False,
            createdAt="2024-05-12T19:26:00Z",
            updatedAt="2024-05-12T19:36:00Z",
        ),
        TaskDB(
            id="task-7",
            title="Call Ruby",
            icon="📞",
            recurrence=None,
            reminderTime=ReminderTime(hour=18, minute=30),
            completed=False,
            createdAt="2024-05-15T18:30:00Z",
            updatedAt="2024-05-15T18:40:00Z",
        ),
        TaskDB(
            id="task-del-1",
            title="Deleted Task 1",
            icon="🗑️",
            reminderTime=ReminderTime(hour=12, minute=0),
            recurrence=None,
            completed=False,
            createdAt="2024-05-20T12:00:00Z",
            updatedAt="2024-05-20T12:10:00Z",
            deleted=True,
        ),
    ],
    user2_id: [
        TaskDB(
            id="task-a1",
            title="Read Book",
            icon="📚",
            recurrence=None,
            reminderTime=ReminderTime(hour=20, minute=30),
            completed=True,
            completedAt="2024-05-11T20:35:00Z",
            createdAt="2024-05-11T20:30:00Z",
            updatedAt="2024-05-11T20:40:00Z",
            completedBy=user2_id,
        ),
        TaskDB(
            id="task-a2",
            title="Meditate",
            icon="🧘",
            recurrence=RecurrenceRule(interval=2, unit=RecurrenceUnit.DAY),
            reminderTime=ReminderTime(hour=7, minute=0),
            completed=False,
            createdAt="2024-05-08T07:00:00Z",
            updatedAt="2024-05-08T07:10:00Z",
        ),
        TaskDB(
            id="task-del-2",
            title="Deleted Task 2",
            icon="🗑️",
            reminderTime=ReminderTime(hour=13, minute=0),
            recurrence=None,
            completed=False,
            createdAt="2024-05-21T13:00:00Z",
            updatedAt="2024-05-21T13:10:00Z",
            deleted=True,
        ),
    ],
}
