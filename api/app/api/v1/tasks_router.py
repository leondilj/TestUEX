"""Endpoints de tasks — contrato em spec/api.md; filtros de lista via query params."""
import uuid

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_task_service
from app.models.task import Task
from app.models.user import User
from app.schemas.task_schema import (
    TaskCreateRequest,
    TaskDetailResponse,
    TaskStatus,
    TaskSummaryResponse,
    TaskUpdateRequest,
)
from app.services.task_service import TaskService

router = APIRouter(tags=["tasks"])


@router.get("/projects/{project_id}/tasks", response_model=list[TaskSummaryResponse])
async def list_tasks(
    project_id: uuid.UUID,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    tag: str | None = None,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[Task]:
    return await task_service.list_tasks(
        project_id,
        current_user.id,
        status=status_filter.value if status_filter else None,
        tag=tag,
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: uuid.UUID,
    payload: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    return await task_service.create_task(
        project_id, current_user.id, payload.model_dump()
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    return await task_service.get_task(task_id, current_user.id)


@router.patch("/tasks/{task_id}", response_model=TaskDetailResponse)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    # exclude_unset: campo omitido não é tocado; campo enviado (mesmo null) é aplicado
    return await task_service.update_task(
        task_id, current_user.id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> None:
    await task_service.delete_task(task_id, current_user.id)
