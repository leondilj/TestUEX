# ADR-003: Assistente roda no mesmo processo da API, sem servidor MCP externo (por enquanto)

**Date:** 2026-07-01
**Status:** Accepted
**Deciders:** Usuário (dono do projeto) + python-architect

---

## Context

O usuário quer, além do escopo mínimo do case, um assistente que conheça projetos/tarefas, crie tarefas e altere status por linguagem natural. A primeira ideia discutida era um servidor MCP real (protocolo stdio/SSE), consumido externamente por Claude Desktop/Claude Code. O usuário decidiu, depois de discutir trade-offs, que: (1) o assistente também precisa ser acessível **dentro do próprio produto** (uma tela "Assistente" no Next.js, para o usuário que prefere linguagem natural em vez de operar manualmente), e (2) por enquanto, **nada de infraestrutura externa** — o assistente deve rodar no mesmo contexto/processo da API.

---

## Decision

O assistente é implementado como **tool use nativo da API Anthropic (Claude)**, orquestrado dentro do próprio processo FastAPI, exposto via `POST /api/v1/assistant/chat`. Não há servidor MCP (protocolo stdio/SSE) nesta fase. As 4 ferramentas (`list_projects`, `list_tasks`, `create_task`, `update_task_status`) são funções Python que chamam diretamente os `services` já existentes — a mesma camada que os routers REST usam — escopadas ao usuário autenticado da requisição de chat (reaproveita o mesmo cookie de sessão do `ADR-001`, sem usuário fixo/token separado).

---

## Options Considered

### Option 1: Tool use in-process via API Anthropic (escolhida)

O `assistant_service` chama a API da Anthropic com as tools definidas em `spec/tools.md`; quando o modelo pede uma tool, a própria API executa a função Python correspondente, no mesmo processo.

**Pros:**
- Zero infraestrutura nova — mesmo processo, mesmo deploy, mesma autenticação por cookie já existente
- Ferramentas chamam `services` diretamente (sem HTTP interno, sem round-trip) — mais rápido e mais simples de testar
- Naturalmente escopado ao usuário logado — não precisa de usuário demo fixo nem de login programático

**Cons:**
- Não é um servidor MCP de verdade — não pode ser conectado por Claude Desktop/Claude Code como um MCP host externo
- Acoplado ao processo da API — não escala nem é reaproveitável fora do Taskly sem refatoração

### Option 2: Servidor MCP externo (protocolo stdio/SSE), consumido por Claude Desktop/Code

**Pros:**
- Demonstra conhecimento do protocolo MCP formal — mais alinhado ao vocabulário técnico da vaga
- Reaproveitável por qualquer MCP host, não só o Taskly

**Cons:**
- Exige processo separado, transporte (stdio/SSE), e um mecanismo de autenticação novo (usuário demo fixo ou token) já que não há sessão de browser
- Não resolve o pedido do usuário de ter uma tela de chat **dentro do produto** — precisaria de um cliente MCP embutido na API para isso, dobrando a complexidade
- Maior risco dentro do prazo de 3 dias

### Option 3: Híbrido — tools compartilhadas, dois adaptadores (in-process + MCP externo)

Módulo de tools único, reaproveitado por um adaptador MCP (externo) e um adaptador de chat interno.

**Pros:**
- Cobre os dois casos de uso (produto + host externo) com lógica de tool não duplicada

**Cons:**
- Complexidade adicional não solicitada agora — o usuário foi explícito: **"nada de externo, por enquanto"**
- Pode ser adotado depois, evoluindo a Option 1, sem retrabalho do núcleo (as funções de tool já ficam isoladas em `app/assistant/tools/`)

---

## Rationale

O usuário priorizou explicitamente a tela de chat dentro do produto e pediu para não introduzir infraestrutura externa agora. A Option 1 entrega exatamente isso com o menor custo de implementação dentro do prazo de 3 dias, e mantém as tools isoladas em módulos próprios (`app/assistant/tools/`) — o que preserva a possibilidade de evoluir para a Option 3 depois, sem redesenhar nada, caso o usuário queira suporte a Claude Desktop/Code no futuro.

---

## Consequences

**Positive:**
- Sem autenticação nova, sem processo novo, sem custo de infraestrutura adicional
- Tools reaproveitam a mesma regra de negócio e autorização por usuário já validada nos endpoints REST

**Negative / Trade-offs:**
- Não é "MCP" no sentido estrito do protocolo — é tool use da API Anthropic. Importante deixar isso claro no README/vídeo para não gerar expectativa errada sobre o que foi implementado.
- Se no futuro quiserem conectar Claude Desktop/Code, será necessário um adaptador MCP adicional (Option 3) — não é retrabalho, é extensão.

**Risks:**
- Alucinação do assistente — mitigado por `spec/prompts.md` (regras explícitas de tool-first, resolução de IDs, nunca afirmar sucesso sem tool call confirmada).
- Custo/latência de chamadas à API da Anthropic — mitigado recomendando um modelo leve (ex: Claude Haiku) para este caso de uso, já que as tools são simples.

---

## Implementation Notes

- SDK: `anthropic` (Python), chamado a partir de `assistant_service.py`
- System prompt fica versionado em `spec/prompts.md` (fonte da verdade) e espelhado em `app/assistant/system_prompt.py`
- Cada tool é uma função isolada em `app/assistant/tools/`, recebendo a sessão do usuário autenticado e delegando ao `service` correspondente — nunca acessando repository diretamente (mantém a mesma separação de camadas do resto da API)
- `tool_calls` executados são sempre retornados na resposta de `POST /assistant/chat` para a UI exibir de forma transparente o que foi feito

---

## Nota de complemento (2026-07-01) — persistência de histórico e limite de iterações

Revisão pós-aceite identificou duas lacunas de implementação não cobertas na decisão original:

1. **Histórico de conversa não estava modelado.** `POST /assistant/chat` recebe `conversation_id`, mas nenhuma tabela armazenava as mensagens. Guardar em memória do processo não é seguro para o caso: qualquer restart da API (comum durante o próprio desenvolvimento/gravação do vídeo) perde a conversa, e não há garantia de que o processo que recebe a mensagem N seja o mesmo que recebeu a mensagem 1. Decisão: persistir em duas tabelas simples, `assistant_conversations` e `assistant_messages` (ver `spec/data-model.md`), seguindo o mesmo padrão `router → service → repository` já usado no resto da API. Isso não contradiz a Option 1 original — é a forma de implementá-la corretamente, não uma nova alternativa.
2. **Sem limite de iterações no loop de tool use.** O `assistant_service` chama a API da Anthropic, executa a tool pedida, devolve o resultado, e repete até haver resposta final em texto — sem um teto explícito. O system prompt (`spec/prompts.md`) reduz bastante o risco (resolve IDs com no máximo 1-2 tools antes de agir), mas um teto explícito é uma proteção barata contra custo/loop descontrolado. Decisão: `assistant_service` limita a **5 iterações de tool call por mensagem**; se exceder, retorna erro amigável (`502` ou mensagem de fallback) em vez de continuar indefinidamente.

---

## References

- `spec/tools.md` — definição completa das 4 ferramentas
- `spec/prompts.md` — regras de comportamento e anti-alucinação
- `ADR-001` — estratégia de autenticação reaproveitada pelo endpoint de chat
