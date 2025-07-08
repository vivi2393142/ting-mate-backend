from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, conint

DayOfWeek = Annotated[int, conint(ge=0, le=6)]
DayOfMonth = Annotated[int, conint(ge=1, le=31)]


class RecurrenceUnit(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class RecurrenceRule(BaseModel):
    interval: int = Field(
        gt=0,
        description="Number of units between recurrences, should be greater than 0",
    )
    unit: RecurrenceUnit
    days_of_week: Optional[List[DayOfWeek]] = None  # 0=Monday, 6=Sunday
    days_of_month: Optional[List[DayOfMonth]] = None


class ReminderTime(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class Task(BaseModel):
    id: str
    title: str
    icon: str  # emoji
    reminder_time: ReminderTime
    recurrence: Optional[RecurrenceRule] = None
    completed: bool
    created_at: datetime
    created_by: str  # user id
    updated_at: datetime
    updated_by: str  # user id
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None  # user id


class TaskDB(Task):
    deleted: bool = False  # internal use only


class UpdateTaskFields(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    reminder_time: Optional[ReminderTime] = None
    recurrence: Optional[RecurrenceRule] = None
    completed: Optional[bool] = None


class UpdateTaskRequest(BaseModel):
    id: str
    updates: UpdateTaskFields


class UpdateTaskStatusRequest(BaseModel):
    completed: bool


class CreateTaskRequest(BaseModel):
    title: str
    icon: str
    reminder_time: ReminderTime
    recurrence: Optional[RecurrenceRule] = None


# Response models for API
class TaskListResponse(BaseModel):
    tasks: List[Task]


class TaskResponse(BaseModel):
    task: Task
