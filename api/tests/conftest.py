"""Fixtures de teste — app + Postgres real + client autenticado (spec/architecture.md).

Os testes rodam contra um banco Postgres dedicado (`taskly_test` por default),
nunca contra o banco de dev. `TEST_DATABASE_URL` sobrescreve o destino (CI).
"""
import os
import tempfile

# Ambiente configurado ANTES de importar a app — Settings/engine leem no import
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://taskly:taskly@localhost:5432/taskly_test",
)
os.environ.setdefault("JWT_SECRET", "test-secret")
# Uploads de teste em diretório temporário — nunca no uploads/ real
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="taskly_test_uploads_")

import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database import async_session_maker
from app.database import engine as app_engine
from app.main import app
from app.models.base import Base
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

TEST_USER = {"email": "tester@example.com", "password": "senha-forte-123"}
OTHER_USER = {"email": "other@example.com", "password": "senha-forte-456"}


async def _ensure_test_database() -> None:
    """Cria o banco de teste se ainda não existir (idempotente)."""
    url = os.environ["DATABASE_URL"]
    base_url, db_name = url.rsplit("/", 1)
    admin = create_async_engine(f"{base_url}/postgres", isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin.dispose()


@pytest.fixture
async def db_schema():
    """Schema recriado do zero a cada teste — isolamento total entre testes."""
    await _ensure_test_database()
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    # O engine da app é global — sem dispose, o pool reaproveitaria conexões
    # presas ao event loop do teste anterior (pytest-asyncio cria um loop por teste)
    await app_engine.dispose()


@pytest.fixture
async def client(db_schema):
    """Client HTTP anônimo apontando para a app (sem servidor de verdade)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_client(client):
    """Client com sessão válida — TEST_USER registrado e logado (cookie no jar)."""
    resp = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert resp.status_code == 201, resp.text
    resp = await client.post("/api/v1/auth/login", json=TEST_USER)
    assert resp.status_code == 200, resp.text
    return client


@pytest.fixture
async def db_session(db_schema):
    """Sessão async crua — para testar tools/services isolados, sem passar por HTTP."""
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def user_id(db_session) -> uuid.UUID:
    """Usuário real persistido (via AuthService, não HTTP) — dono dos fixtures de tool."""
    auth_service = AuthService(UserRepository(db_session))
    user = await auth_service.register(**TEST_USER)
    return user.id


@pytest.fixture
async def other_auth_client(db_schema):
    """Segundo usuário logado, com cookie jar próprio — para testes cross-user (404)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/api/v1/auth/register", json=OTHER_USER)
        assert resp.status_code == 201, resp.text
        resp = await c.post("/api/v1/auth/login", json=OTHER_USER)
        assert resp.status_code == 200, resp.text
        yield c
