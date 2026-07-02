"""Testes de auth (T12) — registro, login, sessão (`me`) e logout.

Contrato em spec/api.md; acceptance criteria de T09 em spec/tasks.md.
"""
from tests.conftest import TEST_USER

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"


# --- POST /auth/register ---


async def test_register_returns_201_without_leaking_password(client):
    resp = await client.post(REGISTER, json=TEST_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == TEST_USER["email"]
    assert "id" in body
    # Acceptance criteria (T09): a senha nunca é retornada em texto puro
    assert TEST_USER["password"] not in resp.text
    assert "password" not in body

async def test_register_duplicate_email_returns_409(client):
    await client.post(REGISTER, json=TEST_USER)
    resp = await client.post(REGISTER, json=TEST_USER)
    assert resp.status_code == 409


async def test_register_email_is_case_insensitive_for_duplicates(client):
    await client.post(REGISTER, json=TEST_USER)
    resp = await client.post(
        REGISTER,
        json={"email": TEST_USER["email"].upper(), "password": "outra-senha-8"},
    )
    assert resp.status_code == 409


async def test_register_short_password_returns_400_without_echo(client):
    resp = await client.post(
        REGISTER, json={"email": "x@example.com", "password": "curta"}
    )
    assert resp.status_code == 400
    assert "curta" not in resp.text  # senha rejeitada não pode ser ecoada


async def test_register_invalid_email_returns_400(client):
    resp = await client.post(
        REGISTER, json={"email": "nao-e-email", "password": "senha-forte-123"}
    )
    assert resp.status_code == 400


# --- POST /auth/login ---


async def test_login_sets_httponly_session_cookie(client):
    await client.post(REGISTER, json=TEST_USER)
    resp = await client.post(LOGIN, json=TEST_USER)
    assert resp.status_code == 200
    assert resp.json()["email"] == TEST_USER["email"]
    set_cookie = resp.headers["set-cookie"]
    assert "taskly_session=" in set_cookie
    assert "HttpOnly" in set_cookie


async def test_login_wrong_password_returns_401(client):
    await client.post(REGISTER, json=TEST_USER)
    resp = await client.post(
        LOGIN, json={"email": TEST_USER["email"], "password": "senha-errada!"}
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client):
    resp = await client.post(
        LOGIN, json={"email": "ghost@example.com", "password": "senha-forte-123"}
    )
    assert resp.status_code == 401


# --- GET /auth/me ---


async def test_me_with_valid_session_returns_user(auth_client):
    resp = await auth_client.get(ME)
    assert resp.status_code == 200
    assert resp.json()["email"] == TEST_USER["email"]


async def test_me_without_session_returns_401(client):
    resp = await client.get(ME)
    assert resp.status_code == 401


async def test_me_with_tampered_cookie_returns_401(client):
    client.cookies.set("taskly_session", "abc.def.ghi")
    resp = await client.get(ME)
    assert resp.status_code == 401


# --- POST /auth/logout ---


async def test_logout_clears_session(auth_client):
    resp = await auth_client.post(LOGOUT)
    assert resp.status_code == 204
    resp = await auth_client.get(ME)
    assert resp.status_code == 401
