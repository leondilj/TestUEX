"""Tool list_tasks — spec/tools.md. Chama task_service, nunca o repository direto."""
import uuid

from app.exceptions.domain_exceptions import DomainError
from app.schemas.task_schema import TaskStatus
from app.services.task_service import TaskService


async def list_tasks(
    task_service: TaskService,
    user_id: uuid.UUID,
    project_id: str,
    status: str | None = None,
    tag: str | None = None,
) -> list[dict] | dict:
    """Retorna um dict com `error` (nunca levanta exceção) quando o input do
    modelo é inválido ou o projeto não é encontrado — spec/prompts.md exige
    reportar isso ao usuário sem inventar alternativas."""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return {"error": f"project_id inválido: {project_id}"}

    if status is not None:
        try:
            status = TaskStatus(status).value
        except ValueError:
            return {"error": f"status inválido: {status}"}

    try:
        tasks = await task_service.list_tasks(
            project_uuid, user_id, status=status, tag=tag
        )
    except DomainError as exc:
        return {"error": str(exc)}

    return [
        {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "tags": task.tags,
        }
        for task in tasks
    ]
