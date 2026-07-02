"""Testes de attachments (T25) — upload, validações (tipo/tamanho), download, delete,
404 cross-user. Contrato em spec/api.md; limites em config.py (spec/data-model.md).
"""
import io
import uuid

PROJECTS = "/api/v1/projects"
ATTACHMENTS = "/api/v1/attachments"

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"


async def _create_task(client) -> dict:
    resp = await client.post(PROJECTS, json={"name": "Website redesign"})
    assert resp.status_code == 201, resp.text
    project = resp.json()
    resp = await client.post(
        f"{PROJECTS}/{project['id']}/tasks", json={"title": "Tarefa com anexos"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _png_upload(filename: str = "mockup.png") -> dict:
    return {"file": (filename, io.BytesIO(PNG_BYTES), "image/png")}


async def _upload(client, task_id: str, **kwargs) -> dict:
    resp = await client.post(
        f"/api/v1/tasks/{task_id}/attachments", files=_png_upload(**kwargs)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- Auth obrigatória ---


async def test_attachments_without_session_returns_401(client):
    resp = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/attachments")
    assert resp.status_code == 401


# --- POST /tasks/{id}/attachments ---


async def test_upload_valid_file_returns_201_with_contract_fields(auth_client):
    task = await _create_task(auth_client)
    body = await _upload(auth_client, task["id"])
    assert body["filename"] == "mockup.png"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(PNG_BYTES)
    assert body["url"] == f"{ATTACHMENTS}/{body['id']}/download"


async def test_upload_disallowed_type_returns_400(auth_client):
    task = await _create_task(auth_client)
    resp = await auth_client.post(
        f"/api/v1/tasks/{task['id']}/attachments",
        files={"file": ("script.exe", io.BytesIO(b"MZ..."), "application/x-msdownload")},
    )
    assert resp.status_code == 400


async def test_upload_oversized_file_returns_400(auth_client):
    task = await _create_task(auth_client)
    too_big = b"x" * (10 * 1024 * 1024 + 1)  # limite de config.py: 10MB
    resp = await auth_client.post(
        f"/api/v1/tasks/{task['id']}/attachments",
        files={"file": ("grande.png", io.BytesIO(too_big), "image/png")},
    )
    assert resp.status_code == 400


async def test_upload_without_file_returns_400(auth_client):
    task = await _create_task(auth_client)
    resp = await auth_client.post(f"/api/v1/tasks/{task['id']}/attachments")
    assert resp.status_code == 400


async def test_upload_to_unknown_task_returns_404(auth_client):
    resp = await auth_client.post(
        f"/api/v1/tasks/{uuid.uuid4()}/attachments", files=_png_upload()
    )
    assert resp.status_code == 404


async def test_upload_to_task_of_another_user_returns_404(
    auth_client, other_auth_client
):
    task = await _create_task(auth_client)
    resp = await other_auth_client.post(
        f"/api/v1/tasks/{task['id']}/attachments", files=_png_upload()
    )
    assert resp.status_code == 404


async def test_upload_strips_path_from_filename(auth_client):
    """Path traversal no nome do arquivo nunca chega ao disco."""
    task = await _create_task(auth_client)
    body = await _upload(auth_client, task["id"], filename="../../etc/passwd.png")
    assert body["filename"] == "passwd.png"


# --- GET /tasks/{id}/attachments ---


async def test_list_attachments_returns_uploaded_files(auth_client):
    task = await _create_task(auth_client)
    await _upload(auth_client, task["id"], filename="a.png")
    await _upload(auth_client, task["id"], filename="b.png")

    resp = await auth_client.get(f"/api/v1/tasks/{task['id']}/attachments")
    assert resp.status_code == 200
    assert [a["filename"] for a in resp.json()] == ["a.png", "b.png"]


async def test_list_attachments_of_another_users_task_returns_404(
    auth_client, other_auth_client
):
    task = await _create_task(auth_client)
    resp = await other_auth_client.get(f"/api/v1/tasks/{task['id']}/attachments")
    assert resp.status_code == 404


# --- GET /attachments/{id}/download ---


async def test_download_returns_file_with_content_type(auth_client):
    task = await _create_task(auth_client)
    attachment = await _upload(auth_client, task["id"])
    resp = await auth_client.get(f"{ATTACHMENTS}/{attachment['id']}/download")
    assert resp.status_code == 200
    assert resp.content == PNG_BYTES
    assert resp.headers["content-type"] == "image/png"


async def test_download_of_another_users_attachment_returns_404(
    auth_client, other_auth_client
):
    task = await _create_task(auth_client)
    attachment = await _upload(auth_client, task["id"])
    resp = await other_auth_client.get(f"{ATTACHMENTS}/{attachment['id']}/download")
    assert resp.status_code == 404


# --- DELETE /attachments/{id} ---


async def test_delete_attachment_returns_204_and_download_404(auth_client):
    task = await _create_task(auth_client)
    attachment = await _upload(auth_client, task["id"])
    resp = await auth_client.delete(f"{ATTACHMENTS}/{attachment['id']}")
    assert resp.status_code == 204
    resp = await auth_client.get(f"{ATTACHMENTS}/{attachment['id']}/download")
    assert resp.status_code == 404


async def test_delete_attachment_of_another_user_returns_404(
    auth_client, other_auth_client
):
    task = await _create_task(auth_client)
    attachment = await _upload(auth_client, task["id"])
    resp = await other_auth_client.delete(f"{ATTACHMENTS}/{attachment['id']}")
    assert resp.status_code == 404
    resp = await auth_client.get(f"{ATTACHMENTS}/{attachment['id']}/download")
    assert resp.status_code == 200
