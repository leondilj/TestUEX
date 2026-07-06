"""Testes HTTP de POST /assistant/chat (T50 — fechando lacuna de cobertura).

T47/T48 testam tools e assistant_service isolados via chamada Python direta;
nenhum teste exercitava o endpoint de verdade (auth wiring, validação 400,
handler AssistantError->502). Aqui o client HTTP é real (auth_client/client de
conftest.py) e só a camada do SDK da Anthropic é substituída, via
app.dependency_overrides em get_assistant_service — nunca uma chamada real.
"""
from types import SimpleNamespace

import pytest
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_assistant_service, get_db
from app.main import app
from app.repositories.assistant_conversation_repository import (
    AssistantConversationRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.assistant_service import AssistantService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

CHAT = "/api/v1/assistant/chat"


class _FakeMessages:
    def __init__(self, responses: list) -> None:
        self._responses = list(responses)

    async def create(self, **kwargs):
        return self._responses.pop(0)


def _fake_client(responses: list) -> SimpleNamespace:
    return SimpleNamespace(messages=_FakeMessages(responses))


def _text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
    )


class _FailingMessages:
    async def create(self, **kwargs):
        from app.exceptions.domain_exceptions import AssistantError

        # simula qualquer falha da SDK sem depender de construir uma exceção
        # real da lib (já coberto em test_assistant_service.py) — o service
        # só precisa levantar algo não capturado por ele mesmo para o teste
        # de handler; aqui usamos o próprio AssistantError como atalho.
        raise AssistantError("Falha simulada da API da Anthropic")


@pytest.fixture
def override_assistant_service():
    """Troca só o client Anthropic do AssistantService — resto real (T50)."""

    def _set(responses: list | None = None, failing: bool = False):
        def override(db: AsyncSession = Depends(get_db)) -> AssistantService:
            client = SimpleNamespace(messages=_FailingMessages()) if failing else _fake_client(responses or [])
            return AssistantService(
                AssistantConversationRepository(db),
                ProjectService(ProjectRepository(db)),
                TaskService(TaskRepository(db), ProjectRepository(db)),
                anthropic_client=client,
            )

        app.dependency_overrides[get_assistant_service] = override

    yield _set
    app.dependency_overrides.pop(get_assistant_service, None)


async def test_assistant_chat_without_session_returns_401(client):
    resp = await client.post(CHAT, json={"message": "oi", "conversation_id": None})
    assert resp.status_code == 401


async def test_assistant_chat_empty_message_returns_400(auth_client):
    resp = await auth_client.post(
        CHAT, json={"message": "   ", "conversation_id": None}
    )
    assert resp.status_code == 400


async def test_assistant_chat_happy_path_returns_200(
    auth_client, override_assistant_service
):
    override_assistant_service([_text_response("Olá! Como posso ajudar?")])

    resp = await auth_client.post(
        CHAT, json={"message": "oi", "conversation_id": None}
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["reply"] == "Olá! Como posso ajudar?"
    assert body["tool_calls"] == []
    assert "conversation_id" in body


async def test_assistant_chat_reuses_conversation_id(
    auth_client, override_assistant_service
):
    override_assistant_service([_text_response("primeira"), _text_response("segunda")])

    first = await auth_client.post(
        CHAT, json={"message": "oi", "conversation_id": None}
    )
    conversation_id = first.json()["conversation_id"]

    second = await auth_client.post(
        CHAT, json={"message": "de novo", "conversation_id": conversation_id}
    )

    assert second.status_code == 200, second.text
    assert second.json()["conversation_id"] == conversation_id


async def test_assistant_chat_upstream_failure_returns_502(
    auth_client, override_assistant_service
):
    override_assistant_service(failing=True)

    resp = await auth_client.post(
        CHAT, json={"message": "oi", "conversation_id": None}
    )

    assert resp.status_code == 502
