"""Acesso a dados de Task — escopo por usuário via join com Project (spec/api.md)."""
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[Task]:
        """Ordenação fixa por created_at ASC — mais antiga primeiro (ADR-004)."""
        query = select(Task).where(Task.project_id == project_id)
        if status is not None:
            query = query.where(Task.status == status)
        if tag is not None:
            query = query.where(Task.tags.any(tag))
        result = await self._session.execute(query.order_by(Task.created_at.asc()))
        return list(result.scalars().all())

    async def get_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        """Join com Project filtra o dono — tarefa de outro usuário nunca é retornada."""
        result = await self._session.execute(
            select(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Task.id == task_id, Project.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, project_id: uuid.UUID, **fields: Any) -> Task:
        task = Task(project_id=project_id, **fields)
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def update(self, task: Task, fields: dict[str, Any]) -> Task:
        for key, value in fields.items():
            setattr(task, key, value)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self._session.delete(task)
        await self._session.commit()
