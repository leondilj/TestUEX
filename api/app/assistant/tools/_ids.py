"""Parsing de UUID compartilhado pelas tools do assistente (spec/tools.md).

Não é uma tool em si — nunca é registrada em ANTHROPIC_TOOLS/assistant_service.
"""
import uuid


def parse_uuid(value: str) -> uuid.UUID | None:
    """`None` quando `value` não é um UUID válido — cada tool decide a mensagem
    de erro (inclui o nome do campo, ex: `task_id`, `project_id`)."""
    try:
        return uuid.UUID(value)
    except ValueError:
        return None
