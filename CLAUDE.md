# Taskly

Teste técnico para a vaga de Desenvolvedor Fullstack na UEX Startup Studio. Ver `spec/product.md` para a visão de produto e `UEX Teste Técnico Vaga Dev Fullstack.md` para o enunciado original do case.

## Stack
- **Backend:** Python + FastAPI, PostgreSQL (via Docker), testes com pytest
- **Frontend:** Next.js (TypeScript)
- **Infra local:** Docker Compose (API + Postgres; Next.js pode rodar fora do compose em dev)
- **Deploy:** não obrigatório (case pede link "se possível"; no rubric conta só nos 10 pts de "além do escopo mínimo", junto com testes extras e performance). Prioridade é **local-first**: `docker-compose` + README que rodam de primeira. Deploy real (ex: Vercel + Railway/Render) só é perseguido se sobrar tempo após escopo mínimo, testes e documentação
- **CI/CD:** GitHub Actions (lint + testes + build) — diferencial priorizado pelo usuário
- **Assistente (extensão):** Anthropic Claude API (tool use), rodando no mesmo processo da API FastAPI — sem servidor MCP externo por enquanto (ver `ADR-003`)
- **Explicitamente fora da stack:** MongoDB, Redis (decisão do usuário, para não consumir tempo do prazo); servidor MCP externo/stdio (adiado, ver `ADR-003`)

## Agents relevantes
- **python-architect** — já gerou `spec/architecture.md`, `spec/data-model.md`, `spec/api.md`, `spec/tools.md`, `spec/prompts.md` para o backend FastAPI e a extensão do assistente
- **python-developer** — implementa endpoints, autenticação, CRUD de projetos/tarefas e o `assistant_service`/tools
- **ai-engineer** — apoia no tool-use loop com a API Anthropic e no ajuste fino do system prompt (`spec/prompts.md`) contra alucinação
- **python-test-engineer** — testes pytest (diferencial priorizado pelo usuário), incluindo as tools do assistente isoladas
- **frontend-engineer** — implementa o Next.js (lista/kanban, toggle, formulários, upload de anexos, tela "Assistente"/chat)
- **ux-developer** — decisões de UX; o case avalia isso explicitamente ("surpreenda-nos" em identidade visual e navegação)
- **devops-engineer** — Docker Compose, GitHub Actions, deploy (se perseguido)
- **code-reviewer** — revisão de backend e frontend antes da entrega
- **project-manager** — quebra o backlog em `spec/tasks.md` sequenciado dentro do prazo de 3 dias

## Convenções
- Backend em camadas: `api` (routers) → `services` → `repositories` → `models`, nunca pulando camada (ver `spec/architecture.md` — "Patterns & Conventions")
- Nomenclatura: `<resource>_router.py`, `<resource>_service.py`, `<resource>_repository.py`, `<resource>_schema.py`
- Toda alteração de schema via migration do Alembic — nunca alterar tabela manualmente
- Toda tool do assistente é uma função isolada em `app/assistant/tools/`, chamando o `service` correspondente — nunca acessando `repository` diretamente

## Arquitetura
- Monorepo: `/api` (FastAPI) e `/web` (Next.js) na raiz do projeto — ver árvore completa em `spec/architecture.md`
- PostgreSQL como único banco de dados
- Autenticação: JWT em cookie `httpOnly` (`ADR-001`); reaproveitada pelo endpoint do assistente — sem mecanismo de auth separado
- Tags da tarefa: coluna `text[]` nativa do Postgres, sem tabela relacional própria (`ADR-002`)
- Assistente: tool use da API Anthropic in-process, 4 ferramentas MVP (`spec/tools.md`), regras anti-alucinação em `spec/prompts.md` (`ADR-003`)

## Contexto de negócio
- Prazo de entrega: **3 dias corridos** a partir do início do case
- Critérios de avaliação (100 pts): Funcionalidade e completude (30) · Qualidade de código/arquitetura (20) · Uso de IA no desenvolvimento (20) · Documentação — README/Spec/prompts (15) · Vídeo e comunicação técnica (5) · Além do escopo mínimo (10)
- Entregáveis: repositório público no GitHub, README + Spec técnica + registro de prompts de IA, vídeo de arquitetura/decisões demonstrando a aplicação (canal principal de prova de funcionamento), documentação do uso de IA. Link de deploy é opcional ("se possível")
- Uso de IA deve ser documentado de forma rastreável (ferramentas, prompts relevantes, onde o output foi revisado/corrigido)
- O assistente in-app (tela "Assistente") é diferencial fora do escopo mínimo — só deve ser implementado depois do escopo obrigatório, testes e documentação estarem prontos
