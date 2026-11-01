from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WebhookCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]


class WebhookAcceptRead(BaseModel):
    result: str


class EventRead(BaseModel):
    id: int
    event_id: str
    type: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    id: int
    event_id: int
    status: str
    attempts: int
    next_run_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsRead(BaseModel):
    events_by_type: dict[str, int]
    tasks_by_status: dict[str, int]
