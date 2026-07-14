# ADR-005: Observabilidade do assistente via Langfuse, self-host local

**Date:** 2026-07-13
**Status:** Accepted
**Deciders:** Usuário (dono do projeto)

---

## Context

O `ADR-003` já registrava como risco aceito o custo/latência das chamadas à API da Anthropic dentro do loop de tool use (`assistant_service._run_tool_loop`, limitado a `MAX_TOOL_ITERATIONS = 5`). Hoje esse loop é uma caixa-preta em runtime: a única visibilidade é o resultado final (`reply` + `tool_calls`) devolvido por `POST /assistant/chat` — não há como inspecionar quantas iterações uma mensagem levou, quantos tokens cada chamada consumiu, ou qual tool foi chamada com qual input, fora de logs manuais. O usuário pediu observabilidade via Langfuse (tracing de LLM) para cobrir essa lacuna, como diferencial "além do escopo mínimo" (assistente já está com T42–T50 completos).

---

## Decision

Instrumentar `assistant_service.py` com o SDK Python do Langfuse (`langfuse==4.14.0`, baseado em OpenTelemetry):

- `chat()` decorado com `@observe(name="assistant_chat")`, envolvendo o corpo com `propagate_attributes(user_id=..., session_id=<conversation_id>)` — toda trace fica filtrável por usuário e por conversa no dashboard.
- `_create_message()` (chamada ao `anthropic.AsyncAnthropic.messages.create`) decorado com `@observe(as_type="generation")`, reportando `model`, input/output e `usage_details` (tokens de input/output) — visibilidade direta de custo por iteração do loop.
- `_execute_tool()` decorado com `@observe(as_type="tool")`, reportando nome da tool, input e resultado — visibilidade de quais tools o modelo chamou e em que ordem, útil para depurar a regra de resolução de IDs (`spec/tools.md` — "Regra transversal").

O servidor Langfuse roda **self-host, local, via Docker Compose** — não Langfuse Cloud —, em um compose **separado** do principal: `docker-compose.langfuse.yml`, subido à parte (`docker compose -f docker-compose.langfuse.yml --env-file .env.langfuse up -d`). O `api` do compose principal aponta para ele via `LANGFUSE_HOST=http://host.docker.internal:3001` (porta remapeada para não colidir com o `web` em dev, que usa 3000). Chaves (`LANGFUSE_PUBLIC_KEY`/`SECRET_KEY`) vazias desabilitam o tracing automaticamente (client em modo no-op) — mesmo padrão já usado para `ANTHROPIC_API_KEY`.

---

## Options Considered

### Option 1: Self-host local via Docker Compose separado (escolhida)

**Pros:**
- Nenhum dado sai da máquina do desenvolvedor/avaliador — sem dependência de conta externa
- Compose isolado do principal — não arrisca o `docker-compose up` do escopo mínimo (prioridade nº 1 do README)
- Decisão explícita do usuário

**Cons:**
- Stack pesada para o que se ganha: a imagem oficial do Langfuse self-host (v3) exige Postgres próprio + ClickHouse + Redis/Valkey + storage S3-compatible (MinIO) — 6 containers a mais rodando localmente
- O projeto já tinha decidido explicitamente **não usar Redis** na própria stack (ver README — "Explicitamente fora da stack") para não consumir tempo do prazo; aqui o Redis é infraestrutura interna do Langfuse, isolada em rede/compose próprios — não é o Taskly reintroduzindo Redis na sua arquitetura, mas é infra adicional rodando na mesma máquina
- Setup mais longo (gerar `SALT`/`ENCRYPTION_KEY`/segredos, `.env.langfuse` próprio) do que simplesmente criar uma conta

### Option 2: Langfuse Cloud (free tier)

**Pros:**
- Zero containers novos, zero segredos de infra para gerenciar — só duas API keys
- Setup em minutos

**Cons:**
- Dados de tracing saem para um serviço de terceiros
- Depende de conectividade externa para o assistente funcionar com tracing habilitado

### Option 3: Não instrumentar agora — só logging estruturado simples

**Pros:**
- Zero dependência nova

**Cons:**
- Não dá visão de custo/tokens por chamada nem árvore de trace (mensagem → iterações → tools) — só reconstrução manual a partir de logs
- Não atende o pedido explícito do usuário

---

## Rationale

O usuário priorizou rodar tudo localmente, mesmo sabendo do custo de infraestrutura adicional — decisão explícita, documentada aqui para não ser confundida com uma contradição do `README` (que exclui Redis **da stack do Taskly**, não de ferramentas de observabilidade rodando ao lado). Isolar em `docker-compose.langfuse.yml` (compose e `name:` de projeto próprios) garante que o `docker-compose up` do escopo mínimo continua subindo sozinho, sem essa dependência — Langfuse é estritamente opcional e a ausência das chaves desabilita o tracing sem quebrar o assistente.

---

## Consequences

**Positive:**
- Visibilidade completa do loop de tool use em runtime: tokens, latência e árvore de chamadas por conversa/usuário
- Isolado do escopo mínimo — nenhuma migration, nenhum endpoint, nenhuma dependência nova na API além do SDK `langfuse`
- Desabilitado por padrão (chaves vazias) — clone novo do repositório continua funcionando sem Langfuse configurado

**Negative / Trade-offs:**
- 6 containers a mais para quem optar por habilitar (Postgres, ClickHouse, Redis, MinIO, langfuse-web, langfuse-worker) — tempo de subida e uso de memória local não triviais
- Mais um `.env` (`.env.langfuse`) para gerenciar, com segredos próprios (`SALT`, `ENCRYPTION_KEY`, etc.)

**Risks:**
- Baixo para o escopo mínimo (isolado, opcional). Risco de setup: se o desenvolvedor não gerar `ENCRYPTION_KEY` via `openssl rand -hex 32` (usar o placeholder do exemplo), o Langfuse local ainda sobe, mas com um segredo fraco — aceitável para uso estritamente local/dev.

---

## Implementation Notes

- SDK: `langfuse==4.14.0` (baseado em OpenTelemetry — `@observe`, `propagate_attributes`, `Langfuse().update_current_generation/update_current_span`)
- Cliente singleton em `app/observability.py`, instanciado uma vez a partir de `Settings` (mesmo padrão de `app/database.py` para o engine) — importado por efeito colateral em `app/main.py` antes de qualquer chamada instrumentada
- Configuração em `app/config.py`: `langfuse_public_key`, `langfuse_secret_key`, `langfuse_host` (default `http://host.docker.internal:3001`) — vazio desabilita
- `docker-compose.yml` principal ganhou `extra_hosts: host.docker.internal:host-gateway` no serviço `api`, para a mesma URL funcionar tanto no Docker Desktop (Windows/Mac) quanto no Docker Engine (Linux)
- Testes existentes (`test_assistant_service.py`) não precisam de chaves reais — com `LANGFUSE_PUBLIC_KEY` vazio o cliente fica em modo no-op e os decorators viram passthrough

---

## References

- `ADR-003` — risco de custo/latência do loop de tool use, mitigado por esta decisão
- `spec/tools.md` — regra de resolução de IDs, uma das motivações para rastrear a ordem de chamadas de tools
- `docker-compose.langfuse.yml` / `.env.langfuse.example` — stack self-host
- README — seção "Explicitamente fora da stack" (Redis aqui é infra interna do Langfuse, não da stack do Taskly)
