"""Testes de tasks (T21) — CRUD, 4 status, filtros, ordenação, cross-user 404.

Inclui também o cascade delete de tasks ao excluir projeto (item adiado da T16).
Contrato em spec/api.md; acceptance criteria de T20 em spec/tasks.md.
"""
import uuid

PROJECTS = "/api/v1/projects"
TASKS = "/api/v1/tasks"

ALL_STATUSES = ["not_started", "in_progress", "done", "cancelled"]


async def _create_project(client, name: str = "Website redesign") -> dict:
    resp = await client.post(PROJECTS, json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_task(client, project_id: str, **overrides) -> dict:
    payload = {"title": "Redesenhar tela de login", **overrides}
    resp = await client.post(f"{PROJECTS}/{project_id}/tasks", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- Auth obrigatória ---


async def test_tasks_without_session_returns_401(client):
    resp = await client.get(f"{PROJECTS}/{uuid.uuid4()}/tasks")
    assert resp.status_code == 401


# --- POST /projects/{id}/tasks ---


async def test_create_task_minimal_gets_defaults(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    assert task["status"] == "not_started"
    assert task["tags"] == []
    assert task["short_description"] is None
    assert task["due_date"] is None


async def test_create_task_with_all_fields(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(
        auth_client,
        project["id"],
        short_description="Criar nova proposta de UI",
        full_description="Levantar referências e propor 2 variações",
        due_date="2026-06-28T18:00:00Z",
        tags=["design"],
    )
    assert task["short_description"] == "Criar nova proposta de UI"
    assert task["full_description"] == "Levantar referências e propor 2 variações"
    assert task["due_date"] == "2026-06-28T18:00:00Z"
    assert task["tags"] == ["design"]


async def test_create_task_without_title_returns_400(auth_client):
    project = await _create_project(auth_client)
    resp = await auth_client.post(f"{PROJECTS}/{project['id']}/tasks", json={})
    assert resp.status_code == 400


async def test_create_task_empty_title_returns_400(auth_client):
    project = await _create_project(auth_client)
    resp = await auth_client.post(
        f"{PROJECTS}/{project['id']}/tasks", json={"title": "   "}
    )
    assert resp.status_code == 400


async def test_create_task_in_project_of_another_user_returns_404(
    auth_client, other_auth_client
):
    project = await _create_project(auth_client)
    resp = await other_auth_client.post(
        f"{PROJECTS}/{project['id']}/tasks", json={"title": "invasão"}
    )
    assert resp.status_code == 404


async def test_create_task_normalizes_tags(auth_client):
    """ADR-002: lowercase + strip + dedupe."""
    project = await _create_project(auth_client)
    task = await _create_task(
        auth_client, project["id"], tags=["  Design ", "URGENTE", "design", "  "]
    )
    assert task["tags"] == ["design", "urgente"]


# --- GET /projects/{id}/tasks ---


async def test_list_tasks_ordered_by_created_at_oldest_first(auth_client):
    """ADR-004: ordenação fixa, mais antiga primeiro."""
    project = await _create_project(auth_client)
    for title in ["primeira", "segunda", "terceira"]:
        await _create_task(auth_client, project["id"], title=title)

    resp = await auth_client.get(f"{PROJECTS}/{project['id']}/tasks")
    assert resp.status_code == 200
    assert [t["title"] for t in resp.json()] == ["primeira", "segunda", "terceira"]


async def test_list_tasks_filter_by_status(auth_client):
    """Acceptance criteria (T20): só as tarefas do status filtrado voltam."""
    project = await _create_project(auth_client)
    kept = await _create_task(auth_client, project["id"], title="pendente")
    done = await _create_task(auth_client, project["id"], title="feita")
    await auth_client.patch(f"{TASKS}/{done['id']}", json={"status": "done"})

    resp = await auth_client.get(
        f"{PROJECTS}/{project['id']}/tasks", params={"status": "not_started"}
    )
    body = resp.json()
    assert [t["id"] for t in body] == [kept["id"]]


async def test_list_tasks_filter_by_tag_is_case_insensitive(auth_client):
    project = await _create_project(auth_client)
    tagged = await _create_task(auth_client, project["id"], tags=["design"])
    await _create_task(auth_client, project["id"], title="outra", tags=["backend"])

    resp = await auth_client.get(
        f"{PROJECTS}/{project['id']}/tasks", params={"tag": "DESIGN"}
    )
    assert [t["id"] for t in resp.json()] == [tagged["id"]]


async def test_list_tasks_invalid_status_returns_400(auth_client):
    project = await _create_project(auth_client)
    resp = await auth_client.get(
        f"{PROJECTS}/{project['id']}/tasks", params={"status": "invalido"}
    )
    assert resp.status_code == 400


async def test_list_tasks_of_unknown_project_returns_404(auth_client):
    resp = await auth_client.get(f"{PROJECTS}/{uuid.uuid4()}/tasks")
    assert resp.status_code == 404


async def test_list_tasks_of_another_users_project_returns_404(
    auth_client, other_auth_client
):
    project = await _create_project(auth_client)
    resp = await other_auth_client.get(f"{PROJECTS}/{project['id']}/tasks")
    assert resp.status_code == 404


# --- GET /tasks/{id} ---


async def test_get_task_detail_includes_full_description(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(
        auth_client, project["id"], full_description="Detalhes completos"
    )
    resp = await auth_client.get(f"{TASKS}/{task['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_description"] == "Detalhes completos"
    assert body["project_id"] == project["id"]


async def test_get_task_of_another_user_returns_404(auth_client, other_auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await other_auth_client.get(f"{TASKS}/{task['id']}")
    assert resp.status_code == 404


# --- PATCH /tasks/{id} ---


async def test_patch_accepts_all_four_statuses(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    for value in ALL_STATUSES:
        resp = await auth_client.patch(f"{TASKS}/{task['id']}", json={"status": value})
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == value


async def test_patch_invalid_status_returns_400(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await auth_client.patch(f"{TASKS}/{task['id']}", json={"status": "paused"})
    assert resp.status_code == 400


async def test_patch_updates_every_editable_field(auth_client):
    """Requisito explícito do case: todo campo é editável após a criação."""
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await auth_client.patch(
        f"{TASKS}/{task['id']}",
        json={
            "title": "Novo título",
            "short_description": "Nova curta",
            "full_description": "Nova completa",
            "due_date": "2026-07-04T12:00:00Z",
            "tags": ["Nova "],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Novo título"
    assert body["short_description"] == "Nova curta"
    assert body["full_description"] == "Nova completa"
    assert body["due_date"] == "2026-07-04T12:00:00Z"
    assert body["tags"] == ["nova"]


async def test_patch_partial_does_not_touch_other_fields(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(
        auth_client, project["id"], short_description="mantém", tags=["design"]
    )
    resp = await auth_client.patch(f"{TASKS}/{task['id']}", json={"status": "done"})
    body = resp.json()
    assert body["short_description"] == "mantém"
    assert body["tags"] == ["design"]


async def test_patch_can_clear_optional_field_with_null(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"], short_description="some")
    resp = await auth_client.patch(
        f"{TASKS}/{task['id']}", json={"short_description": None}
    )
    assert resp.status_code == 200
    assert resp.json()["short_description"] is None


async def test_patch_title_null_returns_400(auth_client):
    """spec/api.md: campo obrigatório removido → 400."""
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await auth_client.patch(f"{TASKS}/{task['id']}", json={"title": None})
    assert resp.status_code == 400


async def test_patch_task_of_another_user_returns_404(auth_client, other_auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await other_auth_client.patch(
        f"{TASKS}/{task['id']}", json={"title": "hackeado"}
    )
    assert resp.status_code == 404


# --- DELETE /tasks/{id} ---


async def test_delete_task_returns_204_and_task_disappears(auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await auth_client.delete(f"{TASKS}/{task['id']}")
    assert resp.status_code == 204
    resp = await auth_client.get(f"{TASKS}/{task['id']}")
    assert resp.status_code == 404


async def test_delete_task_of_another_user_returns_404(auth_client, other_auth_client):
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await other_auth_client.delete(f"{TASKS}/{task['id']}")
    assert resp.status_code == 404
    resp = await auth_client.get(f"{TASKS}/{task['id']}")
    assert resp.status_code == 200


# --- Cascade (item adiado da T16) ---


async def test_delete_project_cascades_its_tasks(auth_client):
    """FK ON DELETE CASCADE: excluir o projeto remove as tarefas (spec/api.md)."""
    project = await _create_project(auth_client)
    task = await _create_task(auth_client, project["id"])
    resp = await auth_client.delete(f"{PROJECTS}/{project['id']}")
    assert resp.status_code == 204
    resp = await auth_client.get(f"{TASKS}/{task['id']}")
    assert resp.status_code == 404
