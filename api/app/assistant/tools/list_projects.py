"""Tool list_projects — spec/tools.md. Chama project_service, nunca o repository direto."""
import uuid

from app.services.project_service import ProjectService


async def list_projects(
    project_service: ProjectService, user_id: uuid.UUID
) -> list[dict]:
    """Sem parâmetros de entrada além do usuário da sessão (spec/tools.md)."""
    projects = await project_service.list_projects(user_id)
    return [{"id": str(project.id), "name": project.name} for project in projects]
