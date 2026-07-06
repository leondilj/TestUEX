"""Exceções de domínio — levantadas nos services, convertidas em HTTP só na camada api.

Nunca deixar exceção do SQLAlchemy vazar para a resposta (spec/architecture.md —
Patterns & Conventions).
"""


class DomainError(Exception):
    """Base de toda exceção de domínio. Sem handler específico, vira HTTP 400."""


class NotFoundError(DomainError):
    """Recurso inexistente ou pertencente a outro usuário — vira HTTP 404 (nunca 403,
    para não vazar a existência do recurso)."""


class ConflictError(DomainError):
    """Conflito de estado (ex: e-mail já cadastrado) — vira HTTP 409."""


class InvalidCredentialsError(DomainError):
    """Credenciais ou sessão inválidas — vira HTTP 401."""


class AssistantError(DomainError):
    """Falha ao orquestrar o assistente — API da Anthropic indisponível ou loop de
    tool use excedido (ADR-003). Vira HTTP 502, não 400 (handler próprio em main.py)."""
