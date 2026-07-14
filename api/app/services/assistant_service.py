"""Orquestra Claude (tool use) + histórico persistido + as tools do assistente — ver ADR-003.

Loop: chama a API da Anthropic, executa a tool pedida via app/assistant/tools/,
devolve o resultado ao modelo, repete até haver resposta final em texto ou até
MAX_TOOL_ITERATIONS rounds de tool use (proteção contra custo/loop descontrolado).
"""
import json
import uuid

import anthropic
from langfuse import observe

from app.assistant.system_prompt import SYSTEM_PROMPT
from app.assistant.tools.create_task import create_task
from app.assistant.tools.list_projects import list_projects
from app.assistant.tools.list_tasks import list_tasks
from app.assistant.tools.update_task_due_date import update_task_due_date
from app.assistant.tools.update_task_status import update_task_status
from app.config import get_settings
from app.exceptions.domain_exceptions import AssistantError, NotFoundError
from app.models.assistant_conversation import AssistantConversation
from app.models.task import TASK_STATUSES
from app.observability import (
    AgentIdentity,
    langfuse_client,
    observed_agent_turn,
    record_turn_outcome,
)
from app.repositories.assistant_conversation_repository import (
    AssistantConversationRepository,
)
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

MAX_TOOL_ITERATIONS = 5

# Identidade de observabilidade do agent (ADR-005/ADR-006) — reutilizada por
# observed_agent_turn/record_turn_outcome. Taskly tem um único assistente hoje,
# então uma constante de módulo já cobre o caso; um segundo agent no futuro
# declararia sua própria AgentIdentity e usaria os mesmos helpers.
TASKLY_ASSISTANT = AgentIdentity(name="taskly-assistant", department="product")
TEMPERATURE = 0.0
MAX_TOKENS = 500

ANTHROPIC_TOOLS: list[dict] = [
    {
        "name": "list_projects",
        "description": "Lista os projetos do usuário autenticado.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_tasks",
        "description": (
            "Lista as tarefas de um projeto, com filtro opcional por status ou tag."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "UUID do projeto — resolvido previamente via list_projects",
                },
                "status": {"type": "string", "enum": list(TASK_STATUSES)},
                "tag": {"type": "string"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "create_task",
        "description": "Cria uma nova tarefa em um projeto existente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "UUID do projeto — nunca inventado, deve vir de list_projects",
                },
                "title": {"type": "string"},
                "short_description": {"type": "string"},
                "full_description": {"type": "string"},
                "due_date": {
                    "type": "string",
                    "description": "Data/hora em ISO 8601",
                },
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["project_id", "title"],
        },
    },
    {
        "name": "update_task_status",
        "description": "Atualiza o status de uma tarefa existente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID da tarefa — nunca inventado, deve vir de list_tasks",
                },
                "status": {"type": "string", "enum": list(TASK_STATUSES)},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "update_task_due_date",
        "description": (
            "Atualiza o prazo de uma tarefa existente. O prazo não pode ser "
            "superior a 30 dias a partir de amanhã."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID da tarefa — nunca inventado, deve vir de list_tasks",
                },
                "due_date": {
                    "type": "string",
                    "description": "Data/hora em ISO 8601",
                },
            },
            "required": ["task_id", "due_date"],
        },
    },
]


class AssistantService:
    def __init__(
        self,
        conversation_repository: AssistantConversationRepository,
        project_service: ProjectService,
        task_service: TaskService,
        anthropic_client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        settings = get_settings()
        self._conversations = conversation_repository
        self._project_service = project_service
        self._task_service = task_service
        self._client = anthropic_client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
        self._model = settings.assistant_model

    @observe(name="assistant_chat")
    async def chat(
        self, user_id: uuid.UUID, message: str, conversation_id: uuid.UUID | None
    ) -> dict:
        conversation = await self._resolve_conversation(user_id, conversation_id)

        # user_id/session_id/tags propagam para todas as generations/tools desta
        # trace (chamadas à Anthropic + tools) — ver ADR-005/ADR-006
        with observed_agent_turn(
            agent=TASKLY_ASSISTANT,
            user_id=str(user_id),
            session_id=str(conversation.id),
        ):
            history = await self._conversations.list_messages(conversation.id)
            messages: list[dict] = [
                {"role": m.role, "content": m.content} for m in history
            ]
            messages.append({"role": "user", "content": message})

            reply, tool_calls, tools_used = await self._run_tool_loop(
                messages, user_id
            )

        # Contrato de metadados de observabilidade por resposta — ADR-005/ADR-006
        record_turn_outcome(
            agent=TASKLY_ASSISTANT,
            session_id=str(conversation.id),
            user_id=str(user_id),
            tools_used=tools_used,
            model_parameters={
                "model": self._model,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
            },
        )

        await self._conversations.add_message(conversation, "user", message)
        await self._conversations.add_message(conversation, "assistant", reply)

        return {
            "conversation_id": conversation.id,
            "reply": reply,
            "tool_calls": tool_calls,
        }

    async def _resolve_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID | None
    ) -> AssistantConversation:
        if conversation_id is None:
            return await self._conversations.create(user_id)
        conversation = await self._conversations.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError("Conversa não encontrada")
        return conversation

    async def _run_tool_loop(
        self, messages: list[dict], user_id: uuid.UUID
    ) -> tuple[str, list[dict], list[dict]]:
        tool_calls: list[dict] = []
        tools_used: list[dict] = []
        iterations = 0

        while True:
            response = await self._create_message(messages)

            if response.stop_reason != "tool_use":
                return self._extract_text(response), tool_calls, tools_used

            iterations += 1
            if iterations > MAX_TOOL_ITERATIONS:
                raise AssistantError(
                    "O assistente não conseguiu concluir a solicitação "
                    "(limite de chamadas de ferramenta excedido)"
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": [
                        self._content_block_to_dict(block)
                        for block in response.content
                    ],
                }
            )

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_calls.append({"tool": block.name, "input": block.input})
                result = await self._execute_tool(block.name, block.input, user_id)
                is_error = isinstance(result, dict) and "error" in result
                tools_used.append(
                    {
                        "name": block.name,
                        "status": "error" if is_error else "success",
                        "error": result.get("error") if is_error else None,
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

    @observe(as_type="generation", name="anthropic_messages_create")
    async def _create_message(self, messages: list[dict]) -> anthropic.types.Message:
        try:
            response = await self._client.messages.create(
                model=self._model,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=ANTHROPIC_TOOLS,
                messages=messages,
            )
        except anthropic.APIError as exc:
            raise AssistantError("Falha ao chamar a API da Anthropic") from exc

        usage = getattr(response, "usage", None)
        langfuse_client.update_current_generation(
            model=self._model,
            model_parameters={"temperature": TEMPERATURE, "max_tokens": MAX_TOKENS},
            input=messages,
            output=[self._content_block_to_dict(b) for b in response.content],
            usage_details=(
                {"input": usage.input_tokens, "output": usage.output_tokens}
                if usage is not None
                else None
            ),
        )
        return response

    @observe(as_type="tool", name="execute_tool")
    async def _execute_tool(
        self, name: str, tool_input: dict, user_id: uuid.UUID
    ) -> dict | list[dict]:
        langfuse_client.update_current_span(name=name, input=tool_input)
        result = await self._execute_tool_impl(name, tool_input, user_id)
        is_error = isinstance(result, dict) and "error" in result
        langfuse_client.update_current_span(
            output=result,
            level="ERROR" if is_error else None,
            status_message=result.get("error") if is_error else None,
        )
        return result

    async def _execute_tool_impl(
        self, name: str, tool_input: dict, user_id: uuid.UUID
    ) -> dict | list[dict]:
        if name == "list_projects":
            return await list_projects(self._project_service, user_id)
        if name == "list_tasks":
            return await list_tasks(self._task_service, user_id, **tool_input)
        if name == "create_task":
            return await create_task(self._task_service, user_id, **tool_input)
        if name == "update_task_status":
            return await update_task_status(self._task_service, user_id, **tool_input)
        if name == "update_task_due_date":
            return await update_task_due_date(self._task_service, user_id, **tool_input)
        raise AssistantError(f"Tool desconhecida: {name}")

    @staticmethod
    def _content_block_to_dict(block) -> dict:
        if block.type == "text":
            return {"type": "text", "text": block.text}
        if block.type == "tool_use":
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }
        raise AssistantError(f"Tipo de conteúdo inesperado da API: {block.type}")

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
