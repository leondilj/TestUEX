"""Testes de projects (T16) — CRUD completo, escopo por usuário (404 cross-user).

Contrato em spec/api.md. O cascade delete de tasks ao excluir projeto é coberto
em T21, quando a tabela `tasks` (T18) existir — a FK com ON DELETE CASCADE é
definida na migration da própria tabela `tasks`.
"""
import uuid

PROJECTS = "/api/v1/projects"


async def _create_project(client, name: str = "Website redesign") -> dict:
    resp = await client.post(PROJECTS, json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- Auth obrigatória ---


async def test_projects_without_session_returns_401(client):
    resp = await client.get(PROJECTS)
    assert resp.status_code == 401


# --- POST /projects ---


async def test_create_project_returns_201_with_contract_fields(auth_client):
    body = await _create_project(auth_client)
    assert body["name"] == "Website redesign"
    assert "id" in body
    assert "created_at" in body


async def test_create_project_empty_name_returns_400(auth_client):
    resp = await auth_client.post(PROJECTS, json={"name": ""})
    assert resp.status_code == 400


async def test_create_project_whitespace_name_returns_400(auth_client):
    resp = await auth_client.post(PROJECTS, json={"name": "   "})
    assert resp.status_code == 400


# --- GET /projects ---


async def test_list_projects_starts_empty(auth_client):
    resp = await auth_client.get(PROJECTS)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_projects_returns_only_own_projects(auth_client, other_auth_client):
    await _create_project(auth_client, "Meu projeto")
    await _create_project(other_auth_client, "Projeto alheio")

    resp = await auth_client.get(PROJECTS)
    names = [p["name"] for p in resp.json()]
    assert names == ["Meu projeto"]


# --- GET /projects/{id} ---


async def test_get_project_returns_detail(auth_client):
    created = await _create_project(auth_client)
    resp = await auth_client.get(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_unknown_project_returns_404(auth_client):
    resp = await auth_client.get(f"{PROJECTS}/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_get_project_of_another_user_returns_404(auth_client, other_auth_client):
    created = await _create_project(auth_client)
    resp = await other_auth_client.get(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 404


# --- PATCH /projects/{id} ---


async def test_update_project_name(auth_client):
    created = await _create_project(auth_client)
    resp = await auth_client.patch(
        f"{PROJECTS}/{created['id']}", json={"name": "Novo nome"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Novo nome"


async def test_update_project_empty_name_returns_400(auth_client):
    created = await _create_project(auth_client)
    resp = await auth_client.patch(f"{PROJECTS}/{created['id']}", json={"name": ""})
    assert resp.status_code == 400


async def test_update_project_of_another_user_returns_404(
    auth_client, other_auth_client
):
    created = await _create_project(auth_client)
    resp = await other_auth_client.patch(
        f"{PROJECTS}/{created['id']}", json={"name": "hackeado"}
    )
    assert resp.status_code == 404
    # O projeto do dono permanece intacto
    resp = await auth_client.get(f"{PROJECTS}/{created['id']}")
    assert resp.json()["name"] == "Website redesign"


# --- DELETE /projects/{id} ---


async def test_delete_project_returns_204_and_project_disappears(auth_client):
    created = await _create_project(auth_client)
    resp = await auth_client.delete(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 204
    resp = await auth_client.get(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 404


async def test_delete_project_of_another_user_returns_404_and_keeps_it(
    auth_client, other_auth_client
):
    created = await _create_project(auth_client)
    resp = await other_auth_client.delete(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 404
    resp = await auth_client.get(f"{PROJECTS}/{created['id']}")
    assert resp.status_code == 200
