# ADR-006: Contrato reutilizável de metadados de observabilidade por resposta de agent

**Date:** 2026-07-14
**Status:** Accepted
**Deciders:** Usuário (dono do projeto)

---

## Context

O `ADR-005` instrumentou o `assistant_service.py` com o SDK do Langfuse, mas só cobria `user_id`/`session_id` (via `propagate_attributes`) e tokens/modelo por generation. O usuário pediu um contrato mais completo de metadados por resposta gerada, pensando em observabilidade e auditoria: `session_id`, `user_id`, `agent_name`, `department`, `tools_used` (nome + status de cada tool chamada), `tags` (`[agent_name, department, ambiente]`), `error_level` (explícito em caso de falha de tool ou resposta inesperada), `model_parameters` (model/temperature/max_tokens) e `escalation_flag` (se a decisão foi escalada para revisão humana).

O pedido original usava vocabulário de um sistema multi-agente com departamentos (`sales-agent`, `compliance-agent`, "Kover AI") que não existe no Taskly — confirmado com o usuário que o contrato deveria ser adaptado ao que existe aqui (`ADR-003`: um único assistente, sem estrutura de departamentos/multi-agente), mas construído de forma reutilizável caso um segundo agent apareça no sistema no futuro.

---

## Decision

Extraído para `app/observability.py` (ao lado do cliente Langfuse singleton do `ADR-005`):

- `AgentIdentity` — dataclass congelado (`name`, `department`) que qualquer agent do sistema declara uma vez como constante de módulo. O assistente do Taskly declara `TASKLY_ASSISTANT = AgentIdentity(name="taskly-assistant", department="product")` em `assistant_service.py`.
- `observed_agent_turn(agent, user_id, session_id)` — context manager fino sobre `propagate_attributes`, propagando `user_id`/`session_id`/`tags` (`[agent.name, agent.department, settings.app_environment]`) para toda a árvore de spans da interação. Chamado no início do método decorado com `@observe`, envolvendo o processamento da mensagem.
- `record_turn_outcome(agent, session_id, user_id, tools_used, model_parameters, escalation_flag=False)` — chamado uma vez por resposta, depois que `tools_used` já é conhecido (loop de tool use terminado). Calcula `error_level`/descrição a partir de `tools_used` (`ERROR` se qualquer tool tiver `status == "error"`) e anexa o dicionário completo de metadados ao span atual via `langfuse_client.update_current_span(metadata=..., level=..., status_message=...)`.

`AssistantService._run_tool_loop` passou a devolver também `tools_used: list[dict]` (`{"name", "status", "error"}` por tool chamada nesta resposta) — paralelo ao `tool_calls` já existente (que continua igual, é o que volta na resposta HTTP) e não observado externamente pela API pública.

---

## Options Considered

### Option 1: Helpers reutilizáveis em `app/observability.py` (escolhida)

**Pros:**
- Um segundo agent (se e quando existir) reaproveita `AgentIdentity`/`observed_agent_turn`/`record_turn_outcome` sem duplicar a lógica de tags/error_level/metadata
- `assistant_service.py` fica com a orquestração do tool-use loop, não com o formato do payload de observabilidade — separação de responsabilidade mais clara
- Testável isoladamente do `AssistantService`, se um teste unitário quiser cobrir o helper depois

**Cons:**
- Uma camada de indireção a mais para um único caso de uso hoje

### Option 2: Manter a lógica inline em `assistant_service.py` (rejeitada)

**Pros:**
- Zero abstração nova, tudo num só lugar

**Cons:**
- O usuário pediu explicitamente para pensar em reuso — inline não atende isso se um segundo agent aparecer
- Contrato de metadados (9 campos) misturado com a lógica de tool-use loop, mais difícil de revisar isoladamente

### Option 3: Sistema de registro de agents/departamentos configurável (rejeitada)

Um registro central de agents com departamentos, carregado de config/banco, permitindo múltiplos agents dinâmicos.

**Cons:**
- Taskly não tem — e não pediu — multi-agente; isso é infraestrutura especulativa para um requisito que não existe (`CLAUDE.md` — não introduzir abstração além do necessário)
- O pedido original vinha de um vocabulário de outro sistema (confirmado com o usuário) — não replicar essa complexidade aqui sem necessidade real

---

## Rationale

`AgentIdentity` como dataclass simples + duas funções (`observed_agent_turn`/`record_turn_outcome`) é o menor nível de abstração que atende "pensar em reuso" sem construir um sistema multi-agente que o Taskly não tem. Se um segundo agent surgir, ele importa os mesmos três nomes de `app/observability.py` e declara sua própria `AgentIdentity` — nenhuma mudança nos helpers.

---

## Consequences

**Positive:**
- Contrato de metadados centralizado e testável fora do `assistant_service.py`
- `error_level` capturado tanto por exceção (nível nativo do Langfuse, já coberto pelo `ADR-005`) quanto por falha "silenciosa" de tool (dict `{"error": ...}` sem exceção — ver `spec/tools.md`), que antes não gerava nível de erro na trace
- `escalation_flag` sempre `False` documentado como decisão consciente — Taskly não tem fluxo de revisão humana; vira `True` só quando essa funcionalidade existir de fato

**Negative / Trade-offs:**
- Mais um módulo (`app/observability.py`) com responsabilidade própria — aceitável dado que já existia para o cliente Langfuse (`ADR-005`)

**Risks:**
- Baixo — mudança aditiva sobre o `ADR-005`, cobertura de teste existente (`test_assistant_service.py`) validada sem alteração de contrato HTTP (`tool_calls` da resposta continua igual)

---

## Implementation Notes

- `app/observability.py`: `AgentIdentity`, `observed_agent_turn`, `record_turn_outcome`
- `assistant_service.py`: `TASKLY_ASSISTANT = AgentIdentity(...)`, `_run_tool_loop` retorna `(reply, tool_calls, tools_used)`
- `department` fixo (`"product"`) — Taskly não tem estrutura organizacional real; usar essa constante até existir motivo de negócio para mudar
- `app_environment` (novo em `Settings`, default `"development"`) alimenta a tag de ambiente — trocar para `"production"` se um deploy real usar isso

---

## References

- `ADR-003` — assistente único, sem multi-agente (razão para `AgentIdentity` ser uma constante fixa, não configurável)
- `ADR-005` — cliente Langfuse singleton e instrumentação original do tool-use loop
- `spec/tools.md` — tools retornam `{"error": ...}` sem levantar exceção; motivação para `error_level` derivado de `tools_used`, não só de exceções
