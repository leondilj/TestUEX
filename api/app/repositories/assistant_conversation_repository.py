"""Acesso a dados de AssistantConversation/AssistantMessage — escopo por user_id.

Mensagem é sub-recurso da conversa (spec/data-model.md): não existe
`assistant_message_repository.py` próprio — igual ao par Task/Attachment,
mas aqui a decomposição fica dentro do mesmo arquivo por serem sempre
acessados juntos (histórico de uma conversa) pelo `assistant_service` (T45).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant_conversation import AssistantConversation
from app.models.assistant_message import AssistantMessage


class AssistantConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> AssistantConversation | None:
        """Filtra por dono junto com o id — conversa de outro usuário nunca é retornada."""
        result = await self._session.execute(
            select(AssistantConversation).where(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID) -> AssistantConversation:
        conversation = AssistantConversation(user_id=user_id)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def list_messages(
        self, conversation_id: uuid.UUID
    ) -> list[AssistantMessage]:
        """Ordenado por created_at ASC — reconstrói o histórico enviado ao modelo."""
        result = await self._session.execute(
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def add_message(
        self, conversation: AssistantConversation, role: str, content: str
    ) -> AssistantMessage:
        """Persiste a mensagem e atualiza `updated_at` da conversa (spec/data-model.md).

        Inserir a mensagem não altera a linha da conversa — `onupdate=func.now()`
        só dispara em colunas efetivamente modificadas, então `updated_at` é
        setado explicitamente aqui.
        """
        message = AssistantMessage(
            conversation_id=conversation.id, role=role, content=content
        )
        conversation.updated_at = datetime.now(timezone.utc)
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message
