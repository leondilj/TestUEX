"""Regra de negócio de projects — recurso de outro usuário vira NotFoundError (404)."""
import uuid

from app.exceptions.domain_exceptions import NotFoundError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._projects = project_repository

    async def list_projects(self, user_id: uuid.UUID) -> list[Project]:
        return await self._projects.list_by_user(user_id)

    async def create_project(self, user_id: uuid.UUID, name: str) -> Project:
        return await self._projects.create(user_id=user_id, name=name)

    async def get_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Project:
        project = await self._projects.get_by_id(project_id, user_id)
        if project is None:
            raise NotFoundError("Projeto não encontrado")
        return project

    async def update_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, name: str
    ) -> Project:
        project = await self.get_project(project_id, user_id)
        return await self._projects.update(project, name)

    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        project = await self.get_project(project_id, user_id)
        await self._projects.delete(project)
