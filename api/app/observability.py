"""Cliente Langfuse (singleton do processo) + contrato reutilizável de metadados
de observabilidade por resposta de agent — ver ADR-005/ADR-006.

O cliente é instanciado uma vez, no import deste módulo (mesmo padrão de
`app/database.py` para o engine do SQLAlchemy), para que `@observe()`/`get_client()`
usados pelos serviços de agent reaproveitem este cliente já configurado a partir de
`Settings`, em vez de cada um ler variáveis de ambiente do processo por conta própria.
`langfuse_public_key` vazio (default) deixa o cliente em modo no-op — nenhuma chamada
sai para o Langfuse.

`AgentIdentity` + `observed_agent_turn`/`record_turn_outcome` existem para que um
segundo agent (além do assistente do Taskly) reaproveite o mesmo contrato de
metadados sem duplicar a lógica — hoje só há um agent, mas a interface já é
agent-agnóstica.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from langfuse import Langfuse, propagate_attributes

from app.config import get_settings

settings = get_settings()

langfuse_client = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


@dataclass(frozen=True)
class AgentIdentity:
    """Identidade fixa de um agent para fins de observabilidade (ADR-005/ADR-006).

    Cada agent do sistema declara a sua uma vez (nome + departamento) como
    constante de módulo — não é por request, já que não muda em runtime.
    """

    name: str
    department: str


@contextmanager
def observed_agent_turn(
    *, agent: AgentIdentity, user_id: str, session_id: str
) -> Iterator[None]:
    """Propaga user_id/session_id/tags (agent, departamento, ambiente) para toda
    a árvore de spans desta interação.

    Chamar logo no início do método do agent decorado com `@observe`, envolvendo
    o processamento da mensagem (generations + tool calls) — precisa ser chamado
    antes dos spans filhos existirem, senão eles não herdam os atributos.
    """
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        tags=[agent.name, agent.department, settings.app_environment],
    ):
        yield


def record_turn_outcome(
    *,
    agent: AgentIdentity,
    session_id: str,
    user_id: str,
    tools_used: list[dict],
    model_parameters: dict,
    escalation_flag: bool = False,
) -> None:
    """Anexa ao span atual o contrato de metadados de observabilidade por
    resposta (ADR-005/ADR-006): session/user, agent/departamento, tools chamadas
    (com status de cada uma), tags, error_level (ERROR se alguma tool falhou),
    parâmetros do modelo usado e escalation_flag.

    Chamar uma vez por resposta gerada, depois que `tools_used` já é conhecido
    (ou seja, após o loop de tool use terminar) — reutilizável por qualquer
    agent do sistema, não só o assistente do Taskly.
    """
    failed_tools = [t for t in tools_used if t["status"] == "error"]
    error_level = "ERROR" if failed_tools else None
    error_description = (
        "; ".join(f"{t['name']}: {t['error']}" for t in failed_tools)
        if failed_tools
        else None
    )

    langfuse_client.update_current_span(
        metadata={
            "session_id": session_id,
            "user_id": user_id,
            "agent_name": agent.name,
            "department": agent.department,
            "tools_used": tools_used,
            "tags": [agent.name, agent.department, settings.app_environment],
            "error_level": error_level,
            "model_parameters": model_parameters,
            # Nenhum agent do sistema tem fluxo de escalonamento para revisão
            # humana implementado hoje — default False até essa decisão de
            # negócio existir para algum agent (ver ADR-005).
            "escalation_flag": escalation_flag,
        },
        level=error_level,
        status_message=error_description,
    )
