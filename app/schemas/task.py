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
    daysOfWeek: Optional[List[DayOfWeek]] = None  # 0=Monday, 6=Sunday
    daysOfMonth: Optional[List[DayOfMonth]] = None


class ReminderTime(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class Task(BaseModel):
    id: str
    title: str
    icon: str  # emoji
    reminderTime: ReminderTime
    recurrence: Optional[RecurrenceRule] = None
    completed: bool
    createdAt: datetime  # ISO timestamp
    updatedAt: datetime  # ISO timestamp
    completedAt: Optional[datetime] = None  # ISO timestamp
    completedBy: Optional[str] = None  # user id


class TaskDB(Task):
    deleted: bool = False  # internal use only


class UpdateTaskFields(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    reminderTime: Optional[ReminderTime] = None
    recurrence: Optional[RecurrenceRule] = None


class UpdateTaskRequest(BaseModel):
    id: str
    updates: UpdateTaskFields


class UpdateTaskStatusRequest(BaseModel):
    id: str
    completed: bool


class CreateTaskRequest(BaseModel):
    title: str
    icon: str
    reminderTime: ReminderTime
    recurrence: Optional[RecurrenceRule] = None
