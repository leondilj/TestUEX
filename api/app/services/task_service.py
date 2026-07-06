"""Regra de negócio de tasks — tags normalizadas (ADR-002), escopo por usuário (404)."""
import uuid
from datetime import datetime, time, timedelta, timezone
from typing import Any

from app.exceptions.domain_exceptions import DomainError, NotFoundError
from app.models.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository

MAX_DUE_DATE_WINDOW_DAYS = 30


def _max_assistant_due_date(now: datetime | None = None) -> datetime:
    """Limite superior de prazo permitido ao assistente: fim do 30º dia contado
    a partir de amanhã (dia subsequente a `now`) — restrição própria da tool
    update_task_due_date, não se aplica ao PATCH normal de tarefa."""
    reference = (now or datetime.now(timezone.utc)).date()
    tomorrow = reference + timedelta(days=1)
    last_allowed_day = tomorrow + timedelta(days=MAX_DUE_DATE_WINDOW_DAYS)
    return datetime.combine(last_allowed_day, time.max, tzinfo=timezone.utc)


def _normalize_tags(tags: list[str]) -> list[str]:
    """Lowercase + strip + dedupe preservando ordem (ADR-002)."""
    normalized: list[str] = []
    for tag in tags:
        clean = tag.strip().lower()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


class TaskService:
    def __init__(
        self, task_repository: TaskRepository, project_repository: ProjectRepository
    ) -> None:
        self._tasks = task_repository
        self._projects = project_repository

    async def _ensure_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        if await self._projects.get_by_id(project_id, user_id) is None:
            raise NotFoundError("Projeto não encontrado")

    async def list_tasks(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[Task]:
        await self._ensure_project(project_id, user_id)
        if tag is not None:
            tag = tag.strip().lower()  # tags são persistidas normalizadas
        return await self._tasks.list_by_project(
            project_id, user_id, status=status, tag=tag
        )

    async def create_task(
        self, project_id: uuid.UUID, user_id: uuid.UUID, data: dict[str, Any]
    ) -> Task:
        await self._ensure_project(project_id, user_id)
        data["tags"] = _normalize_tags(data.get("tags") or [])
        return await self._tasks.create(project_id=project_id, **data)

    async def get_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        task = await self._tasks.get_by_id(task_id, user_id)
        if task is None:
            raise NotFoundError("Tarefa não encontrada")
        return task

    async def update_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, updates: dict[str, Any]
    ) -> Task:
        task = await self.get_task(task_id, user_id)
        if "title" in updates and updates["title"] is None:
            raise DomainError("Título é obrigatório e não pode ser removido")
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value
        if "tags" in updates:
            updates["tags"] = _normalize_tags(updates["tags"] or [])
        return await self._tasks.update(task, updates)

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        task = await self.get_task(task_id, user_id)
        await self._tasks.delete(task)

    async def update_task_due_date(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        due_date: datetime,
        now: datetime | None = None,
    ) -> Task:
        """Usada pela tool update_task_due_date do assistente (spec/tools.md) —
        limita o prazo a no máximo 30 dias a partir de amanhã. Restrição exclusiva
        desta operação: o PATCH normal de tarefa (`update_task`) não a aplica.

        `now` é injetável só para testar a fronteira dos 30 dias de forma
        determinística — a tool nunca o informa, sempre usa o relógio real."""
        task = await self.get_task(task_id, user_id)
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        max_due_date = _max_assistant_due_date(now)
        if due_date > max_due_date:
            raise DomainError(
                "Prazo não pode ser superior a 30 dias a partir de amanhã "
                f"(máximo permitido: {max_due_date.isoformat()})"
            )
        return await self._tasks.update(task, {"due_date": due_date})
