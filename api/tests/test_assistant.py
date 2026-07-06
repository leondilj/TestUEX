"""Testes das tools do assistente (T47) — spec/tools.md.

Chamadas diretas às funções de app/assistant/tools/, contra o Postgres de teste
real (via `db_session`/`user_id` de conftest.py) — nunca via HTTP e nunca
chamando a API da Anthropic de verdade (isso é T48, com o SDK mockado no nível
do assistant_service).
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.assistant.tools.create_task import create_task
from app.assistant.tools.list_projects import list_projects
from app.assistant.tools.list_tasks import list_tasks
from app.assistant.tools.update_task_due_date import update_task_due_date
from app.assistant.tools.update_task_status import update_task_status
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


@pytest.fixture
def project_service(db_session) -> ProjectService:
    return ProjectService(ProjectRepository(db_session))


@pytest.fixture
def task_service(db_session) -> TaskService:
    return TaskService(TaskRepository(db_session), ProjectRepository(db_session))


@pytest.fixture
async def project_id(project_service, user_id) -> str:
    project = await project_service.create_project(user_id, "Website redesign")
    return str(project.id)


# --- list_projects ---


async def test_list_projects_empty(project_service, user_id):
    assert await list_projects(project_service, user_id) == []


async def test_list_projects_returns_only_own(project_service, user_id):
    await project_service.create_project(user_id, "Meu projeto")
    other_user_id = uuid.uuid4()  # simula outro usuário — nunca deve vazar aqui

    result = await list_projects(project_service, user_id)

    assert [p["name"] for p in result] == ["Meu projeto"]
    assert all(p["id"] != str(other_user_id) for p in result)


# --- list_tasks ---


async def test_list_tasks_invalid_project_id_returns_error(task_service, user_id):
    result = await list_tasks(task_service, user_id, project_id="not-a-uuid")
    assert "error" in result


async def test_list_tasks_unknown_project_returns_error(task_service, user_id):
    result = await list_tasks(task_service, user_id, project_id=str(uuid.uuid4()))
    assert "error" in result


async def test_list_tasks_invalid_status_returns_error(task_service, user_id, project_id):
    result = await list_tasks(
        task_service, user_id, project_id=project_id, status="banana"
    )
    assert "error" in result


async def test_list_tasks_returns_created_tasks(task_service, user_id, project_id):
    await create_task(task_service, user_id, project_id=project_id, title="Revisar contrato")

    result = await list_tasks(task_service, user_id, project_id=project_id)

    assert len(result) == 1
    assert result[0]["title"] == "Revisar contrato"
    assert result[0]["status"] == "not_started"


async def test_list_tasks_filters_by_status(task_service, user_id, project_id):
    created = await create_task(task_service, user_id, project_id=project_id, title="A")
    await create_task(task_service, user_id, project_id=project_id, title="B")
    await update_task_status(task_service, user_id, task_id=created["id"], status="done")

    result = await list_tasks(
        task_service, user_id, project_id=project_id, status="not_started"
    )

    assert [t["title"] for t in result] == ["B"]


# --- create_task ---


async def test_create_task_success(task_service, user_id, project_id):
    result = await create_task(
        task_service,
        user_id,
        project_id=project_id,
        title="Revisar contrato",
        due_date="2026-07-03T18:00:00Z",
    )
    assert result["title"] == "Revisar contrato"
    assert result["status"] == "not_started"
    assert result["due_date"] == "2026-07-03T18:00:00+00:00"


async def test_create_task_invalid_project_id_returns_error(task_service, user_id):
    result = await create_task(
        task_service, user_id, project_id="not-a-uuid", title="X"
    )
    assert "error" in result


async def test_create_task_unknown_project_returns_error(task_service, user_id):
    result = await create_task(
        task_service, user_id, project_id=str(uuid.uuid4()), title="X"
    )
    assert "error" in result


async def test_create_task_invalid_due_date_returns_error(task_service, user_id, project_id):
    result = await create_task(
        task_service,
        user_id,
        project_id=project_id,
        title="X",
        due_date="sexta-feira",
    )
    assert "error" in result


# --- update_task_status ---


async def test_update_task_status_success(task_service, user_id, project_id):
    created = await create_task(task_service, user_id, project_id=project_id, title="X")

    result = await update_task_status(
        task_service, user_id, task_id=created["id"], status="done"
    )

    assert result == {"id": created["id"], "title": "X", "status": "done"}


async def test_update_task_status_invalid_task_id_returns_error(task_service, user_id):
    result = await update_task_status(
        task_service, user_id, task_id="not-a-uuid", status="done"
    )
    assert "error" in result


async def test_update_task_status_unknown_task_returns_error(task_service, user_id):
    result = await update_task_status(
        task_service, user_id, task_id=str(uuid.uuid4()), status="done"
    )
    assert "error" in result


async def test_update_task_status_invalid_status_returns_error(
    task_service, user_id, project_id
):
    created = await create_task(task_service, user_id, project_id=project_id, title="X")

    result = await update_task_status(
        task_service, user_id, task_id=created["id"], status="banana"
    )
    assert "error" in result


# --- update_task_due_date ---


async def test_update_task_due_date_success(task_service, user_id, project_id):
    created = await create_task(task_service, user_id, project_id=project_id, title="X")
    new_due_date = datetime.now(timezone.utc) + timedelta(days=5)

    result = await update_task_due_date(
        task_service, user_id, task_id=created["id"], due_date=new_due_date.isoformat()
    )

    assert result["id"] == created["id"]
    assert result["title"] == "X"
    assert result["due_date"] == new_due_date.isoformat()


async def test_update_task_due_date_invalid_task_id_returns_error(task_service, user_id):
    result = await update_task_due_date(
        task_service,
        user_id,
        task_id="not-a-uuid",
        due_date=datetime.now(timezone.utc).isoformat(),
    )
    assert "error" in result


async def test_update_task_due_date_unknown_task_returns_error(task_service, user_id):
    result = await update_task_due_date(
        task_service,
        user_id,
        task_id=str(uuid.uuid4()),
        due_date=datetime.now(timezone.utc).isoformat(),
    )
    assert "error" in result


async def test_update_task_due_date_invalid_format_returns_error(
    task_service, user_id, project_id
):
    created = await create_task(task_service, user_id, project_id=project_id, title="X")

    result = await update_task_due_date(
        task_service, user_id, task_id=created["id"], due_date="sexta-feira"
    )
    assert "error" in result


async def test_update_task_due_date_beyond_30_days_from_tomorrow_returns_error(
    task_service, user_id, project_id
):
    created = await create_task(task_service, user_id, project_id=project_id, title="X")
    too_far = datetime.now(timezone.utc) + timedelta(days=40)

    result = await update_task_due_date(
        task_service, user_id, task_id=created["id"], due_date=too_far.isoformat()
    )
    assert "error" in result
