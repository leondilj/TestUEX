"""Schemas de attachments — contrato em spec/api.md."""
import uuid

from pydantic import BaseModel, ConfigDict, computed_field


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int

    @computed_field
    @property
    def url(self) -> str:
        return f"/api/v1/attachments/{self.id}/download"
