"""Endpoint do assistente — POST /assistant/chat (extensão, além do escopo mínimo, ADR-003)."""
from fastapi import APIRouter, Depends

from app.api.deps import get_assistant_service, get_current_user
from app.models.user import User
from app.schemas.assistant_schema import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
async def chat(
    payload: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> dict:
    return await assistant_service.chat(
        current_user.id, payload.message, payload.conversation_id
    )
