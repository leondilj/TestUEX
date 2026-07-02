"""Acesso a dados de Project — toda query escopada a user_id (spec/api.md)."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(self, user_id: uuid.UUID) -> list[Project]:
        result = await self._session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project | None:
        """Filtra por dono junto com o id — projeto de outro usuário nunca é retornado."""
        result = await self._session.execute(
            select(Project).where(
                Project.id == project_id, Project.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, name: str) -> Project:
        project = Project(user_id=user_id, name=name)
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def update(self, project: Project, name: str) -> Project:
        project.name = name
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.commit()
