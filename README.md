# Taskly

Sistema web de gestão de tarefas pessoais — teste técnico para a vaga de Desenvolvedor Fullstack na **UEX Startup Studio**. Enunciado original em [`UEX Teste Técnico Vaga Dev Fullstack.md`](./UEX%20Teste%20Técnico%20Vaga%20Dev%20Fullstack.md).

O usuário cria a própria conta (e-mail/senha), organiza o trabalho em **projetos** e gerencia **tarefas** dentro de cada projeto, alternando livremente entre visualização em **lista** e **kanban**. Cada tarefa tem título, descrição curta e completa, prazo, tags, anexos/fotos e status (`Não iniciada`, `Em andamento`, `Concluída`, `Cancelada`) — todos os campos editáveis após a criação, com filtros por status e tag.

## Status

| Entregável | Situação |
|---|---|
| Escopo mínimo do case (auth, projetos, tarefas lista/kanban, anexos, filtros) | ✅ Implementado e testado |
| Testes automatizados (backend, contra Postgres real) | ✅ 65 testes |
| Revisão de código (quality gate backend + frontend vs. spec) | ✅ T36/T37 |
| CI (GitHub Actions: lint + testes + build) | 🔜 T38 |
| Extensão: tela "Assistente" (Claude tool use) | 🔜 T42–T50 — especificada em `spec/tools.md`/`spec/prompts.md` |
| Deploy | Opcional — só se sobrar tempo (decisão em `spec/product.md`) |

## Como rodar (local-first)

Pré-requisitos: **Docker + Docker Compose** e **Node.js 20+**.

```bash
# 1. Backend + banco — sobe Postgres 16 e a API em http://localhost:8000
#    (migrations Alembic aplicadas automaticamente no startup)
docker compose up -d

# 2. Frontend — http://localhost:3000
cd web
npm install
npm run dev
```

Pronto: abra `http://localhost:3000`, crie uma conta e use. Não é preciso criar `.env` — todos os defaults de desenvolvimento funcionam de primeira (ver tabela abaixo para customizar).

Para habilitar a extensão do assistente (opcional, além do escopo mínimo), crie um `.env` **na raiz do projeto** (mesmo nível do `docker-compose.yml`) com `ANTHROPIC_API_KEY=sk-ant-...` — o Compose lê esse arquivo automaticamente para preencher a variável do container `api`. Sem ele, `docker compose up` sobe normalmente com o chat desabilitado. Rodando a API fora do Docker (ex: testes), a mesma variável vai em `api/.env` (lido pelo pydantic-settings).

A documentação interativa da API (OpenAPI/Swagger) fica em `http://localhost:8000/docs`, e um smoke check de infra em `http://localhost:8000/health`.

### Rodando os testes

Os testes de backend rodam contra um **Postgres real** (nunca SQLite — o comportamento de `text[]` e constraints importa), num banco dedicado `taskly_test` criado automaticamente no mesmo Postgres do compose:

```bash
docker compose up -d postgres     # basta o banco
cd api
pip install -r requirements-dev.txt
python -m pytest
```

Frontend: `cd web && npx tsc --noEmit && npm run lint`.

## Variáveis de ambiente

### API (`api/app/config.py` — pydantic-settings, aceita `.env`)

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | — (definida no compose) | URL asyncpg do Postgres |
| `JWT_SECRET` | — (definida no compose) | Segredo de assinatura do JWT — **trocar fora de dev** |
| `JWT_EXPIRES_DAYS` | `7` | Validade da sessão (sem refresh token — `ADR-001`) |
| `COOKIE_SECURE` | `false` | `true` em produção (cookie só via HTTPS) |
| `COOKIE_SAMESITE` | `lax` | `none` se web e api em domínios diferentes |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Origens permitidas (com credenciais — nunca `*`) |
| `UPLOAD_DIR` | `uploads` | Diretório dos anexos (volume Docker nomeado no compose) |
| `MAX_UPLOAD_BYTES` | `10485760` (10MB) | Limite por arquivo de anexo |
| `ALLOWED_UPLOAD_TYPES` | imagens, PDF, DOC/DOCX, TXT | MIME types aceitos no upload |
| `ANTHROPIC_API_KEY` | `""` | Extensão do assistente (T42+) — vazio desabilita o chat |
| `ASSISTANT_MODEL` | `claude-haiku-4-5-20251001` | Modelo usado pelo assistente — leve/rápido, as tools não exigem raciocínio complexo (`ADR-003`) |

### Web

| Variável | Default | Descrição |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Base URL da API |

## Stack e decisões

| Camada | Tecnologia | Por quê |
|---|---|---|
| Backend | Python + FastAPI, SQLAlchemy 2.0 async + Alembic | Async nativo, validação Pydantic, OpenAPI automático; migrations versionadas |
| Banco | PostgreSQL 16 (Docker) | Requisito da vaga; `text[]` nativo para tags (`ADR-002`) |
| Frontend | Next.js (App Router, TypeScript), Tailwind CSS 4, TanStack Query | Velocidade de construção de UI própria dentro do prazo; cache/estado de servidor prontos |
| Autenticação | JWT em cookie `httpOnly` + bcrypt | Sessão persistente sem expor token a XSS via `localStorage` (`ADR-001`) |
| Testes | pytest + pytest-asyncio + httpx `ASGITransport` | Endpoints reais contra Postgres real, sem mockar o banco |
| Assistente (extensão) | API Anthropic Claude (tool use), in-process | Sem servidor MCP externo por enquanto (`ADR-003`) |

Decisões registradas como ADRs em [`spec/decisions/`](./spec/decisions): autenticação (001), armazenamento de tags (002), assistente in-process (003), kanban **sem drag-and-drop** — mudança de status por controle explícito no card (004).

**Explicitamente fora da stack:** MongoDB e Redis (decisão de escopo para caber no prazo de 3 dias).

## Arquitetura

```
Browser → web (Next.js) → api (FastAPI: routers → services → repositories → models) → PostgreSQL
                                                                                       ↳ uploads/ (anexos, volume Docker)
```

- **Camadas estritas** no backend: `api` (routers) → `services` (regra de negócio) → `repositories` (dados) → `models` — nunca pulando camada; exceções de domínio convertidas em HTTP só na borda
- **Escopo por usuário em profundidade**: toda query de projeto/tarefa/anexo filtra pelo dono; recurso de outro usuário retorna `404` (não `403`, para não vazar existência)
- **Frontend**: lista/kanban são a mesma coleção re-renderizada client-side; mudança de status é otimista com rollback; sessão validada por `GET /auth/me` com redirect automático em qualquer `401`

Diagramas completos (Mermaid) em [`spec/architecture.md`](./spec/architecture.md).

## Estrutura do repositório

```
TestUEX/
├── spec/                    # fonte da verdade — Spec-Driven Development
│   ├── product.md           # visão de produto, usuários, escopo
│   ├── architecture.md      # componentes, diagramas, decisões, riscos
│   ├── api.md               # contrato de todos os endpoints REST
│   ├── data-model.md        # entidades e relacionamentos
│   ├── tools.md             # ferramentas do assistente (extensão)
│   ├── prompts.md           # system prompt do assistente + registro de uso de IA
│   ├── tasks.md             # backlog sequenciado (T01–T53)
│   └── decisions/           # ADR-001 a ADR-004
├── api/                     # backend FastAPI (routers/services/repositories/models)
│   ├── alembic/             # migrations versionadas
│   └── tests/               # suíte pytest contra Postgres real
├── web/                     # frontend Next.js (App Router)
│   ├── app/                 # rotas: (auth)/login|register · (app)/projects/[projectId]
│   ├── components/ui/       # primitivas (dialog nativo, menu, toast, chips…)
│   └── lib/                 # api-client, tipos, query keys
├── ux-spec-*.md             # especificações de UX (navegação/identidade e interações)
├── docker-compose.yml       # api + postgres (web roda via npm run dev em dev)
└── CLAUDE.md                # convenções para agentes de IA neste projeto
```

## Documentação técnica

- [`spec/product.md`](./spec/product.md) — visão de produto, usuários, capacidades, fora de escopo
- [`spec/architecture.md`](./spec/architecture.md) — componentes, fluxo de dados, decisões, riscos
- [`spec/api.md`](./spec/api.md) — contrato completo de endpoints REST
- [`spec/data-model.md`](./spec/data-model.md) — entidades e relacionamentos
- [`ux-spec-navigation-and-identity.md`](./ux-spec-navigation-and-identity.md) / [`ux-spec-task-views-and-form.md`](./ux-spec-task-views-and-form.md) — fluxos, wireframes, identidade visual e interações
- [`spec/tasks.md`](./spec/tasks.md) — backlog sequenciado com dependências e critérios de aceite

## Uso de IA no desenvolvimento

O projeto inteiro — specs, código, testes, revisões — foi desenvolvido com **Claude Code** sobre um pipeline de agentes especializados (arquiteto, UX, desenvolvedor, test engineer, revisor), em Spec-Driven Development: as specs foram geradas e revisadas **antes** do código, e cada commit referencia a task do backlog que implementa.

O registro rastreável — ferramentas, prompts relevantes por fase e **onde o output da IA foi revisado/corrigido por humano ou por revisão adversária** — está em [`spec/prompts.md`](./spec/prompts.md).

## Entregáveis do case

- [x] Repositório público no GitHub
- [x] Spec técnica (`spec/` + UX specs)
- [x] README com setup local-first
- [x] Registro de prompts de IA consolidado (`spec/prompts.md`)
- [x] Implementação do escopo mínimo (`api/`, `web/`)
- [x] Testes automatizados
- [ ] CI (GitHub Actions) — T38
- [ ] Vídeo de arquitetura e demonstração — T41
- [ ] Extensão: tela "Assistente" — T42–T50 (após vídeo)
- [ ] Link de deploy *(opcional)*
