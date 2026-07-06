"""Tool update_task_due_date — spec/tools.md. Chama task_service, nunca o repository direto."""
import uuid
from datetime import datetime

from app.exceptions.domain_exceptions import DomainError
from app.services.task_service import TaskService


async def update_task_due_date(
    task_service: TaskService, user_id: uuid.UUID, task_id: str, due_date: str
) -> dict:
    """Retorna um dict com `error` (nunca levanta exceção) quando o input do
    modelo é inválido, a tarefa não é encontrada ou o prazo ultrapassa a janela
    de 30 dias a partir de amanhã — `task_id` nunca deve ser inventado pelo
    modelo (deve vir de um list_tasks prévio, spec/tools.md)."""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return {"error": f"task_id inválido: {task_id}"}

    try:
        parsed_due_date = datetime.fromisoformat(due_date)
    except ValueError:
        return {"error": f"due_date deve estar em ISO 8601: {due_date}"}

    try:
        task = await task_service.update_task_due_date(
            task_uuid, user_id, parsed_due_date
        )
    except DomainError as exc:
        return {"error": str(exc)}

    return {
        "id": str(task.id),
        "title": task.title,
        "due_date": task.due_date.isoformat() if task.due_date else None,
    }
