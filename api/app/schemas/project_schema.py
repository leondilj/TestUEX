"""Schemas de projects — contrato em spec/api.md (nome vazio → 400)."""
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Strip antes de validar — "   " também é nome vazio
ProjectName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]


class ProjectCreateRequest(BaseModel):
    name: ProjectName


class ProjectUpdateRequest(BaseModel):
    name: ProjectName


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
