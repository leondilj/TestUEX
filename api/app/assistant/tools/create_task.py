"""Tool create_task — spec/tools.md. Chama task_service, nunca o repository direto."""
import uuid
from datetime import datetime

from app.exceptions.domain_exceptions import DomainError
from app.services.task_service import TaskService


async def create_task(
    task_service: TaskService,
    user_id: uuid.UUID,
    project_id: str,
    title: str,
    short_description: str | None = None,
    full_description: str | None = None,
    due_date: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Retorna um dict com `error` (nunca levanta exceção) quando o input do
    modelo é inválido ou o projeto não é encontrado — `project_id` nunca deve
    ser inventado pelo modelo (deve vir de um list_projects prévio, spec/tools.md)."""
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return {"error": f"project_id inválido: {project_id}"}

    parsed_due_date: datetime | None = None
    if due_date is not None:
        try:
            parsed_due_date = datetime.fromisoformat(due_date)
        except ValueError:
            return {"error": f"due_date deve estar em ISO 8601: {due_date}"}

    try:
        task = await task_service.create_task(
            project_uuid,
            user_id,
            {
                "title": title,
                "short_description": short_description,
                "full_description": full_description,
                "due_date": parsed_due_date,
                "tags": tags or [],
            },
        )
    except DomainError as exc:
        return {"error": str(exc)}

    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
    }
