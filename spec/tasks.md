# Tasks — Taskly

Backlog sequenciado a partir de `spec/product.md`, `spec/architecture.md`, `spec/api.md`, `spec/data-model.md`, `spec/tools.md`, `spec/prompts.md` e `spec/decisions/*` (inclui as revisões de `ADR-001`, `ADR-003` e `ADR-004` de 2026-07-01). Prazo: **3 dias corridos**. Ordem de prioridade conforme `CLAUDE.md`: escopo obrigatório → testes → documentação → CI/CD → assistente (extensão) → deploy (opcional).

IDs (`T01`, `T02`...) existem só para referenciar dependências dentro deste documento.

---

## Layer: Setup & Infra

- [x] T01 Criar estrutura de monorepo (`api/`, `web/`, `docker-compose.yml`) conforme `spec/architecture.md` — Priority: P1 | Agent: devops-engineer | Depends on: none
- [x] T02 Configurar `docker-compose.yml` (api + postgres; volume `uploads/`) e `Dockerfile` da API — Priority: P1 | Agent: devops-engineer | Depends on: T01
- [x] T03 Scaffold do projeto FastAPI (`app/main.py`, `config.py`, camadas `api/services/repositories/models/schemas/exceptions/utils`) — Priority: P1 | Agent: python-developer | Depends on: T01
- [ ] T04 Configurar Alembic (`alembic.ini`, `env.py` assíncrono) — Priority: P1 | Agent: python-developer | Depends on: T03
- [ ] T05 Scaffold do projeto Next.js (App Router, TypeScript, Tailwind, TanStack Query) — Priority: P1 | Agent: frontend-engineer | Depends on: T01

**Acceptance criteria (T02):**
```
Given o repositório clonado do zero
When o avaliador roda `docker-compose up`
Then a API sobe conectada ao Postgres, sem erro, na primeira tentativa
```

---

## Layer: Backend — Auth (ADR-001)

- [ ] T06 Migration Alembic da tabela `User` (`spec/data-model.md`) — Priority: P1 | Agent: python-developer | Depends on: T04
- [ ] T07 Implementar `user_repository.py`, `security.py` (hash/verify de senha, criação/validação de JWT) — Priority: P1 | Agent: python-developer | Depends on: T06
- [ ] T08 Implementar `auth_service.py` + `auth_schema.py` (senha mínima 8 chars, ver `ADR-001`) — Priority: P1 | Agent: python-developer | Depends on: T07
- [ ] T09 Implementar `auth_router.py`: `POST /auth/register`, `POST /auth/login` (seta cookie httpOnly), `POST /auth/logout`, `GET /auth/me` — Priority: P1 | Agent: python-developer | Depends on: T08
- [ ] T10 Implementar dependency `get_current_user` em `api/deps.py` (decodifica cookie, 401 se ausente/inválido/expirado) — Priority: P1 | Agent: python-developer | Depends on: T08
- [ ] T11 Configurar CORS (`allow_credentials=True`, origem explícita do `web`) — Priority: P1 | Agent: python-developer | Depends on: T09
- [ ] T12 Testes pytest de `auth`: registro (sucesso/409/400), login (sucesso/401), `me` (sucesso/401), logout — Priority: P1 | Agent: python-test-engineer | Depends on: T09, T10

**Acceptance criteria (T09):**
```
Given um e-mail ainda não cadastrado
When o usuário chama POST /auth/register com e-mail e senha válidos
Then a conta é criada (201) e a senha nunca é retornada ou logada em texto puro
```

---

## Layer: Backend — Projects

- [ ] T13 Migration Alembic da tabela `Project` — Priority: P1 | Agent: python-developer | Depends on: T06
- [ ] T14 Implementar `project_repository.py`, `project_service.py`, `project_schema.py` (todo acesso escopado a `user_id`) — Priority: P1 | Agent: python-developer | Depends on: T13, T10
- [ ] T15 Implementar `projects_router.py`: `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}` — Priority: P1 | Agent: python-developer | Depends on: T14
- [ ] T16 Testes pytest de `projects`: CRUD completo, 404 ao acessar projeto de outro usuário, cascade delete de tasks — Priority: P1 | Agent: python-test-engineer | Depends on: T15

---

## Layer: Backend — Tasks

- [ ] T18 Migration Alembic da tabela `Task` (enum `status`, `text[]` de `tags`, `CHECK` constraint) — Priority: P1 | Agent: python-developer | Depends on: T13
- [ ] T19 Implementar `task_repository.py` (`list_by_project` ordenado por `created_at ASC`, ver `ADR-004`), `task_service.py` (normalização de tags para lowercase/strip, ver `ADR-002`), `task_schema.py` — Priority: P1 | Agent: python-developer | Depends on: T18
- [ ] T20 Implementar `tasks_router.py`: `GET /projects/{id}/tasks` (filtros `status`/`tag`), `POST /projects/{id}/tasks`, `GET/PATCH/DELETE /tasks/{id}` — Priority: P1 | Agent: python-developer | Depends on: T19
- [ ] T21 Testes pytest de `tasks`: CRUD completo, todos os 4 status, filtro por status/tag, edição de qualquer campo, ordenação por `created_at`, 404 cross-user — Priority: P1 | Agent: python-test-engineer | Depends on: T20

**Acceptance criteria (T20 — filtro):**
```
Given um projeto com tarefas em status "not_started" e "done"
When o frontend chama GET /projects/{id}/tasks?status=not_started
Then apenas as tarefas "not_started" são retornadas
```

---

## Layer: Backend — Attachments

- [ ] T22 Migration Alembic da tabela `Attachment` — Priority: P1 | Agent: python-developer | Depends on: T18
- [ ] T23 Implementar `attachment_repository.py`, `attachment_service.py` (limite 10MB, tipos permitidos configuráveis via `config.py`, ver `spec/data-model.md`), `attachment_schema.py` — Priority: P1 | Agent: python-developer | Depends on: T22
- [ ] T24 Implementar `attachments_router.py`: `POST/GET /tasks/{id}/attachments`, `GET /attachments/{id}/download`, `DELETE /attachments/{id}` — Priority: P1 | Agent: python-developer | Depends on: T23
- [ ] T25 Testes pytest de `attachments`: upload válido, tipo/tamanho inválido (400), download, delete, 404 cross-user — Priority: P1 | Agent: python-test-engineer | Depends on: T24

---

## Layer: Frontend — UX

- [ ] T26 Definir fluxo de navegação (auth → lista de projetos → projeto → lista/kanban de tarefas), wireframes de baixa fidelidade e identidade visual — Priority: P1 | Agent: ux-developer | Depends on: none
- [ ] T27 Especificar UX do toggle lista/kanban, do formulário de tarefa (todos os campos editáveis) e do upload de anexos — Priority: P1 | Agent: ux-developer | Depends on: T26

---

## Layer: Frontend — Core

- [ ] T28 Implementar `api-client.ts` (fetch com `credentials: "include"`) e `types.ts` (espelhando `spec/data-model.md`) — Priority: P1 | Agent: frontend-engineer | Depends on: T05
- [ ] T29 Telas de login/cadastro (`(auth)/login`, `(auth)/register`) + guarda de rota autenticada — Priority: P1 | Agent: frontend-engineer | Depends on: T28, T09, T26
- [ ] T30 Lista de projetos (`(app)/projects`) — criar/editar/excluir projeto — Priority: P1 | Agent: frontend-engineer | Depends on: T29, T15
- [ ] T31 Lista/kanban de tarefas (`[projectId]/page.tsx`) com toggle de visualização — Priority: P1 | Agent: frontend-engineer | Depends on: T30, T20, T27
- [ ] T32 Controle de status explícito no card (lista e kanban) — dropdown/botão que chama `PATCH /tasks/{id}` com `{ status }`, sem drag-and-drop (ver `ADR-004`) — Priority: P1 | Agent: frontend-engineer | Depends on: T31
- [ ] T33 Formulário de tarefa (criar/editar todos os campos: título, descrições, prazo, tags) — Priority: P1 | Agent: frontend-engineer | Depends on: T31
- [ ] T34 UI de upload/listagem/remoção de anexos na tarefa — Priority: P1 | Agent: frontend-engineer | Depends on: T33, T24
- [ ] T35 Filtro por status/tag na UI de lista/kanban — Priority: P2 | Agent: frontend-engineer | Depends on: T31

---

## Layer: Quality Gate

- [ ] T36 Revisar backend completo (auth, projects, tasks, attachments) contra `spec/architecture.md` — camadas, exceções de domínio, escopo por usuário — Priority: P1 | Agent: code-reviewer | Depends on: T12, T16, T21, T25
- [ ] T37 Revisar frontend completo contra a especificação de UX (T26/T27) e o contrato da API — Priority: P1 | Agent: code-reviewer | Depends on: T32, T33, T34, T35

---

## Layer: CI/CD

- [ ] T38 Configurar GitHub Actions (`ci.yml`): lint (backend + frontend), pytest contra Postgres efêmero, build de `api` e `web` — Priority: P1 | Agent: devops-engineer | Depends on: T36, T37

---

## Layer: Documentation

- [ ] T39 README com setup local-first (`docker-compose up` + `npm run dev`), variáveis de ambiente, decisões de stack — Priority: P1 | Agent: devops-engineer | Depends on: T38
- [ ] T40 Consolidar/revisar `spec/prompts.md` como registro rastreável de uso de IA (ferramentas, prompts relevantes, onde o output foi revisado) — Priority: P1 | Agent: project-manager | Depends on: T36, T37
- [ ] T41 Gravar vídeo de arquitetura/decisões demonstrando a aplicação (canal principal de prova de funcionamento) — Priority: P1 | Agent: devops-engineer | Depends on: T39

---

## Layer: Extensão — Assistente (ADR-003, só após T36–T41)

- [ ] T42 Migration Alembic de `assistant_conversations` + `assistant_messages` (`spec/data-model.md`) — Priority: P3 | Agent: python-developer | Depends on: T41
- [ ] T43 Implementar `assistant_conversation_repository.py` — Priority: P3 | Agent: python-developer | Depends on: T42
- [ ] T44 Implementar as 4 tools isoladas em `app/assistant/tools/` (`list_projects`, `list_tasks`, `create_task`, `update_task_status`), cada uma chamando o `service` correspondente — nunca `repository` diretamente (ver `CLAUDE.md` — Convenções) — Priority: P3 | Agent: ai-engineer | Depends on: T15, T20
- [ ] T45 Implementar `assistant_service.py`: monta system prompt (`spec/prompts.md`) + histórico persistido + tools, chama API Anthropic, loop de tool use limitado a 5 iterações (`ADR-003`), persiste mensagens — Priority: P3 | Agent: ai-engineer | Depends on: T43, T44
- [ ] T46 Implementar `assistant_router.py`: `POST /assistant/chat` — Priority: P3 | Agent: python-developer | Depends on: T45
- [ ] T47 Testes das 4 tools isoladas (sem chamar a API da Anthropic de verdade — mockar só a camada do SDK, nunca o `service`) — Priority: P3 | Agent: python-test-engineer | Depends on: T44
- [ ] T48 Testes do `assistant_service` (resolução de IDs, limite de iterações, anti-alucinação conforme regras de `spec/prompts.md`) — Priority: P3 | Agent: python-test-engineer | Depends on: T45
- [ ] T49 Tela "Assistente" (chat) no `web`, exibindo `tool_calls` de forma transparente — Priority: P3 | Agent: frontend-engineer | Depends on: T46, T26
- [ ] T50 Revisão final do assistente (prompt anti-alucinação, isolamento das tools, cobertura de teste) — Priority: P3 | Agent: code-reviewer | Depends on: T47, T48, T49

---

## Layer: Opcional — Deploy (só se sobrar tempo após T01–T50)

- [ ] T51 Deploy do `web` na Vercel — Priority: P4 | Agent: devops-engineer | Depends on: T39
- [ ] T52 Deploy da `api` + Postgres (Railway/Render) — atenção a `SameSite=None; Secure` no cookie (`ADR-001`) e a anexos em disco não sobreviverem a filesystem efêmero (`spec/architecture.md` — Risks) — Priority: P4 | Agent: devops-engineer | Depends on: T39
- [ ] T53 Atualizar README com link de deploy — Priority: P4 | Agent: devops-engineer | Depends on: T51, T52

---

## Sequenciamento sugerido (3 dias corridos)

- **Dia 1:** T01–T25 (infra + backend completo: auth, projects, tasks, attachments + testes de cada um) + T26–T27 (UX) em paralelo
- **Dia 2:** T28–T35 (frontend completo) + T36–T38 (review + CI/CD)
- **Dia 3 (manhã):** T39–T41 (README, prompts.md, vídeo) — escopo mínimo entregável fechado aqui
- **Dia 3 (tarde, se sobrar tempo):** T42–T50 (assistente) → T51–T53 (deploy, só se ainda sobrar tempo)

---

## Dependencies

- Todo o backend de `tasks`/`attachments` depende de `projects` (T13–T16) e `auth` (T06–T12) estarem prontos
- Frontend (T28+) depende do contrato de API estar implementado (não só especificado) para evitar retrabalho — trabalhar com mocks baseados em `spec/api.md` é aceitável para começar em paralelo no Dia 1, mas T30+ precisa dos endpoints reais
- A extensão do assistente (T42+) depende explicitamente do escopo mínimo, testes e documentação estarem prontos (T01–T41) — não priorizar antes disso (regra explícita do usuário em `CLAUDE.md`)

## Blockers / Open Questions

- [UNCLEAR] Limite de projetos/tarefas por usuário — `spec/product.md` deixa em aberto. Não bloqueia desenvolvimento: assumir ilimitado por padrão (nenhuma validação de teto) a menos que o usuário decida o contrário.

**Resolvido nesta revisão:** o bloqueio anterior sobre reordenação de `position` no kanban (drag-and-drop) foi eliminado pelo `ADR-004` — decisão do usuário de não implementar drag-and-drop neste momento. O campo `position` foi removido do modelo (`spec/data-model.md`); a ordenação agora é fixa por `created_at` e a mudança de status é feita por um controle explícito no card (T32).
