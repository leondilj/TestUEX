"""Tool update_task_status — spec/tools.md. Chama task_service, nunca o repository direto."""
import uuid

from app.exceptions.domain_exceptions import DomainError
from app.schemas.task_schema import TaskStatus
from app.services.task_service import TaskService


async def update_task_status(
    task_service: TaskService, user_id: uuid.UUID, task_id: str, status: str
) -> dict:
    """Retorna um dict com `error` (nunca levanta exceção) quando o input do
    modelo é inválido ou a tarefa não é encontrada — `task_id` nunca deve ser
    inventado pelo modelo (deve vir de um list_tasks prévio, spec/tools.md)."""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return {"error": f"task_id inválido: {task_id}"}

    try:
        status_enum = TaskStatus(status)
    except ValueError:
        return {"error": f"status inválido: {status}"}

    try:
        task = await task_service.update_task(
            task_uuid, user_id, {"status": status_enum}
        )
    except DomainError as exc:
        return {"error": str(exc)}

    return {"id": str(task.id), "title": task.title, "status": task.status}
