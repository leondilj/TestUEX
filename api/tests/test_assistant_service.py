"""Testes do AssistantService (T48) — spec/prompts.md, ADR-003.

Cobre resolução de conversa (nova vs. existente, cross-user), o loop de tool
use (execução, transparência de tool_calls, limite de iterações) e os
mecanismos de código que sustentam as regras anti-alucinação de
spec/prompts.md (system prompt sempre enviado, erro de tool nunca escondido
do modelo). Mocka só a camada do SDK da Anthropic — os services/repositories
são reais, contra o Postgres de teste (nunca a API da Anthropic de verdade).
"""
import uuid
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from app.assistant.system_prompt import SYSTEM_PROMPT
from app.exceptions.domain_exceptions import AssistantError, NotFoundError
from app.repositories.assistant_conversation_repository import (
    AssistantConversationRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.assistant_service import MAX_TOOL_ITERATIONS, AssistantService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


@pytest.fixture
def conversation_repository(db_session):
    return AssistantConversationRepository(db_session)


@pytest.fixture
def project_service(db_session) -> ProjectService:
    return ProjectService(ProjectRepository(db_session))


@pytest.fixture
def task_service(db_session) -> TaskService:
    return TaskService(TaskRepository(db_session), ProjectRepository(db_session))


class _FakeMessages:
    """Substitui client.messages da SDK — nunca chama a API de verdade."""

    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeMessages esgotado — chamadas além do esperado")
        return self._responses.pop(0)


def _fake_client(responses: list) -> SimpleNamespace:
    return SimpleNamespace(messages=_FakeMessages(responses))


def _text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=text)],
    )


def _tool_use_response(tool_id: str, name: str, tool_input: dict) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[
            SimpleNamespace(type="tool_use", id=tool_id, name=name, input=tool_input)
        ],
    )


def _make_service(
    conversation_repository, project_service, task_service, responses: list
) -> AssistantService:
    return AssistantService(
        conversation_repository,
        project_service,
        task_service,
        anthropic_client=_fake_client(responses),
    )


# --- Resolução de conversa ---


async def test_chat_creates_conversation_when_id_is_none(
    conversation_repository, project_service, task_service, user_id
):
    service = _make_service(
        conversation_repository, project_service, task_service, [_text_response("oi")]
    )

    result = await service.chat(user_id, "oi", None)

    conversation = await conversation_repository.get_by_id(
        result["conversation_id"], user_id
    )
    assert conversation is not None


async def test_chat_reuses_existing_conversation_and_sends_history(
    conversation_repository, project_service, task_service, user_id
):
    conversation = await conversation_repository.create(user_id)
    await conversation_repository.add_message(conversation, "user", "oi")
    await conversation_repository.add_message(
        conversation, "assistant", "Olá! Como posso ajudar?"
    )
    service = _make_service(
        conversation_repository,
        project_service,
        task_service,
        [_text_response("Tudo bem, e você?")],
    )

    result = await service.chat(user_id, "tudo bem?", conversation.id)

    assert result["conversation_id"] == conversation.id
    sent_messages = service._client.messages.calls[0]["messages"]
    assert sent_messages == [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "Olá! Como posso ajudar?"},
        {"role": "user", "content": "tudo bem?"},
    ]


async def test_chat_with_conversation_from_another_user_raises_not_found(
    conversation_repository, project_service, task_service, user_id, other_user_id
):
    conversation = await conversation_repository.create(other_user_id)
    service = _make_service(conversation_repository, project_service, task_service, [])

    with pytest.raises(NotFoundError):
        await service.chat(user_id, "oi", conversation.id)


async def test_chat_with_unknown_conversation_id_raises_not_found(
    conversation_repository, project_service, task_service, user_id
):
    service = _make_service(conversation_repository, project_service, task_service, [])

    with pytest.raises(NotFoundError):
        await service.chat(user_id, "oi", uuid.uuid4())


# --- Loop de tool use ---


async def test_chat_executes_tool_and_returns_final_reply(
    conversation_repository, project_service, task_service, user_id
):
    await project_service.create_project(user_id, "Website redesign")
    service = _make_service(
        conversation_repository,
        project_service,
        task_service,
        [
            _tool_use_response("t1", "list_projects", {}),
            _text_response("Você tem 1 projeto: Website redesign."),
        ],
    )

    result = await service.chat(user_id, "quais projetos eu tenho?", None)

    assert result["reply"] == "Você tem 1 projeto: Website redesign."
    assert result["tool_calls"] == [{"tool": "list_projects", "input": {}}]


async def test_chat_persists_user_and_assistant_messages(
    conversation_repository, project_service, task_service, user_id
):
    service = _make_service(
        conversation_repository,
        project_service,
        task_service,
        [_text_response("Olá!")],
    )

    result = await service.chat(user_id, "oi", None)

    history = await conversation_repository.list_messages(result["conversation_id"])
    assert [(m.role, m.content) for m in history] == [("user", "oi"), ("assistant", "Olá!")]


async def test_chat_raises_assistant_error_when_max_iterations_exceeded(
    conversation_repository, project_service, task_service, user_id
):
    responses = [
        _tool_use_response(f"t{i}", "list_projects", {})
        for i in range(MAX_TOOL_ITERATIONS + 1)
    ]
    service = _make_service(
        conversation_repository, project_service, task_service, responses
    )

    with pytest.raises(AssistantError):
        await service.chat(user_id, "loop", None)

    assert len(service._client.messages.calls) == MAX_TOOL_ITERATIONS + 1


async def test_chat_raises_assistant_error_for_unknown_tool(
    conversation_repository, project_service, task_service, user_id
):
    service = _make_service(
        conversation_repository,
        project_service,
        task_service,
        [_tool_use_response("t1", "delete_everything", {})],
    )

    with pytest.raises(AssistantError):
        await service.chat(user_id, "faz algo estranho", None)


async def test_chat_wraps_anthropic_api_error_as_assistant_error(
    conversation_repository, project_service, task_service, user_id
):
    class _FailingMessages:
        async def create(self, **kwargs):
            raise anthropic.APIConnectionError(
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            )

    client = SimpleNamespace(messages=_FailingMessages())
    service = AssistantService(
        conversation_repository, project_service, task_service, anthropic_client=client
    )

    with pytest.raises(AssistantError):
        await service.chat(user_id, "oi", None)


# --- Anti-alucinação (spec/prompts.md) ---


async def test_chat_always_sends_system_prompt(
    conversation_repository, project_service, task_service, user_id
):
    service = _make_service(
        conversation_repository, project_service, task_service, [_text_response("oi")]
    )

    await service.chat(user_id, "oi", None)

    assert service._client.messages.calls[0]["system"] == SYSTEM_PROMPT


async def test_chat_marks_failed_tool_result_as_is_error(
    conversation_repository, project_service, task_service, user_id
):
    """Projeto inexistente: a tool retorna {"error": ...}, nunca dado inventado —
    o tool_result precisa chegar ao modelo marcado como erro, nunca como sucesso."""
    service = _make_service(
        conversation_repository,
        project_service,
        task_service,
        [
            _tool_use_response(
                "t1", "list_tasks", {"project_id": str(uuid.uuid4())}
            ),
            _text_response("Não encontrei esse projeto."),
        ],
    )

    result = await service.chat(user_id, "tarefas do projeto X", None)

    assert result["reply"] == "Não encontrei esse projeto."
    tool_result_message = service._client.messages.calls[1]["messages"][-1]
    tool_result_block = tool_result_message["content"][0]
    assert tool_result_block["is_error"] is True
    assert "error" in tool_result_block["content"]
