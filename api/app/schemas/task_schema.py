"""Schemas de tasks — contrato em spec/api.md; enum de status em spec/data-model.md."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.attachment_schema import AttachmentResponse


class TaskStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


TaskTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]


class TaskCreateRequest(BaseModel):
    title: TaskTitle
    short_description: str | None = Field(default=None, max_length=280)
    full_description: str | None = None
    due_date: datetime | None = None
    tags: list[str] = []


class TaskUpdateRequest(BaseModel):
    """PATCH parcial — só os campos presentes no payload são aplicados
    (`model_dump(exclude_unset=True)` no router). `title: null` é rejeitado no service."""

    title: TaskTitle | None = None
    short_description: str | None = Field(default=None, max_length=280)
    full_description: str | None = None
    due_date: datetime | None = None
    status: TaskStatus | None = None
    tags: list[str] | None = None


class TaskSummaryResponse(BaseModel):
    """Formato da lista/kanban (spec/api.md) — sem `full_description`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    short_description: str | None
    due_date: datetime | None
    status: TaskStatus
    tags: list[str]
    created_at: datetime


class TaskDetailResponse(TaskSummaryResponse):
    """Detalhe completo — inclui anexos (spec/api.md, GET /tasks/{id})."""

    project_id: uuid.UUID
    full_description: str | None
    updated_at: datetime
    attachments: list[AttachmentResponse] = []
