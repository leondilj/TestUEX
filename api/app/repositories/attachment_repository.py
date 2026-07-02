"""Acesso a dados de Attachment — escopo por usuário via join Task→Project."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.models.project import Project
from app.models.task import Task


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_task(self, task_id: uuid.UUID) -> list[Attachment]:
        result = await self._session.execute(
            select(Attachment)
            .where(Attachment.task_id == task_id)
            .order_by(Attachment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, attachment_id: uuid.UUID, user_id: uuid.UUID
    ) -> Attachment | None:
        """Join até Project filtra o dono — anexo de outro usuário nunca é retornado."""
        result = await self._session.execute(
            select(Attachment)
            .join(Task, Attachment.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(Attachment.id == attachment_id, Project.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        task_id: uuid.UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> Attachment:
        attachment = Attachment(
            task_id=task_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        self._session.add(attachment)
        await self._session.commit()
        await self._session.refresh(attachment)
        return attachment

    async def delete(self, attachment: Attachment) -> None:
        await self._session.delete(attachment)
        await self._session.commit()
