"""Schemas do assistente — contrato em spec/api.md (mensagem vazia → 400, ADR-003)."""
import uuid
from typing import Annotated

from pydantic import BaseModel, StringConstraints

# Strip antes de validar — "   " também é mensagem vazia
AssistantMessageText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]


class AssistantChatRequest(BaseModel):
    message: AssistantMessageText
    conversation_id: uuid.UUID | None = None


class AssistantChatResponse(BaseModel):
    conversation_id: uuid.UUID
    reply: str
    tool_calls: list[dict]
