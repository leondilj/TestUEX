# Taskly

Sistema web de gestão de tarefas pessoais — teste técnico para a vaga de Desenvolvedor Fullstack na **UEX Startup Studio**. Enunciado original em [`UEX Teste Técnico Vaga Dev Fullstack.md`](./UEX%20Teste%20Técnico%20Vaga%20Dev%20Fullstack.md).

## Status atual

🚧 **Fase de especificação (Spec-Driven Development) — implementação ainda não iniciada.**

Todo o projeto foi planejado antes de qualquer linha de código: visão de produto, arquitetura, contrato de API, modelo de dados, decisões técnicas (ADRs) e backlog sequenciado já estão prontos em [`spec/`](./spec). O código de `api/` (FastAPI) e `web/` (Next.js) ainda não existe neste repositório — as instruções de instalação/execução abaixo descrevem o que **vai** existir, conforme `spec/architecture.md` e `spec/tasks.md`.

## O que é o Taskly

O usuário cria sua própria conta (e-mail/senha, sem OAuth), organiza o trabalho em projetos e gerencia tarefas dentro de cada projeto, alternando entre visualização em lista e kanban. Cada tarefa tem título, descrições curta e completa, prazo, tags, anexos/fotos e status (`Não iniciada`, `Em andamento`, `Concluída`, `Cancelada`) — todos os campos editáveis após a criação.

Como extensão além do escopo mínimo do case, o Taskly terá uma tela **"Assistente"**: um chat que usa a API da Anthropic (Claude, tool use) para consultar, criar tarefas e mudar status por linguagem natural, rodando no mesmo processo da API. Ver `spec/product.md` (seção "Extensão além do escopo mínimo") e `ADR-003`.

## Stack definida

| Camada | Tecnologia |
|---|---|
| Backend | Python + FastAPI, SQLAlchemy 2.0 (async) + Alembic |
| Banco de dados | PostgreSQL 16 (via Docker) |
| Frontend | Next.js 14+ (App Router, TypeScript), Tailwind CSS, TanStack Query |
| Autenticação | JWT em cookie `httpOnly` (`ADR-001`) |
| Assistente (extensão) | API Anthropic Claude (tool use), in-process — sem servidor MCP externo por enquanto (`ADR-003`) |
| Testes | pytest + pytest-asyncio + `httpx.AsyncClient`, contra Postgres real |
| CI/CD | GitHub Actions (lint + testes + build) |
| Infra local | Docker Compose (api + postgres; web roda fora do compose em dev) |

Detalhes completos e justificativas em `spec/architecture.md` (Technology Decisions) e nos ADRs em `spec/decisions/`.

## Arquitetura

Diagramas completos (visão geral do sistema e fluxo do Assistente) em [`spec/architecture.md`](./spec/architecture.md#system-overview). Resumo:

```
Browser → web (Next.js) → api (FastAPI: routers → services → repositories → models) → PostgreSQL
                                                                                       ↳ uploads/ (anexos)
```

O Assistente roda dentro do mesmo processo da `api`, chamando a API da Anthropic com tool use sobre as mesmas `services` usadas pelos endpoints REST.

## Estrutura do repositório

```
TestUEX/
├── spec/                         # fonte da verdade — Spec-Driven Development
│   ├── product.md                # visão de produto, usuários, escopo
│   ├── architecture.md           # componentes, diagramas, decisões de tecnologia, riscos
│   ├── api.md                    # contrato de todos os endpoints REST
│   ├── data-model.md             # entidades e relacionamentos
│   ├── tools.md                  # ferramentas do assistente (extensão)
│   ├── prompts.md                # system prompt do assistente + registro de uso de IA
│   ├── tasks.md                  # backlog sequenciado (3 dias)
│   └── decisions/                # ADRs (auth, tags, assistente in-process, kanban sem drag-and-drop)
├── api/                           # backend FastAPI — ainda não implementado
├── web/                           # frontend Next.js — ainda não implementado
├── docker-compose.yml             # planejado — ver spec/tasks.md (T01/T02)
├── CLAUDE.md                      # convenções e stack para agentes/assistentes de IA neste projeto
└── UEX Teste Técnico Vaga Dev Fullstack.md   # enunciado original do case
```

## Como rodar (planejado)

Ainda não aplicável — `api/` e `web/` não existem neste repositório. Quando implementado (ver `spec/tasks.md`, Setup & Infra), o fluxo será:

```bash
# Backend + banco
docker-compose up

# Frontend (fora do compose em dev)
cd web
npm install
npm run dev
```

Pré-requisitos previstos: Docker, Docker Compose, Node.js 18+, uma chave de API da Anthropic (`ANTHROPIC_API_KEY`) para a extensão do assistente.

## Documentação técnica

- [`spec/product.md`](./spec/product.md) — visão de produto, usuários, capacidades, fora de escopo, suposições
- [`spec/architecture.md`](./spec/architecture.md) — componentes, diagramas Mermaid, fluxo de dados, decisões de tecnologia, riscos
- [`spec/api.md`](./spec/api.md) — contrato completo de endpoints REST
- [`spec/data-model.md`](./spec/data-model.md) — entidades e relacionamentos
- [`spec/tools.md`](./spec/tools.md) / [`spec/prompts.md`](./spec/prompts.md) — ferramentas e system prompt do assistente
- [`spec/tasks.md`](./spec/tasks.md) — backlog sequenciado dentro do prazo de 3 dias
- [`spec/decisions/`](./spec/decisions) — ADRs: estratégia de autenticação (001), armazenamento de tags (002), assistente in-process (003), kanban sem drag-and-drop (004)

## Uso de IA no desenvolvimento

Este projeto foi planejado inteiramente com apoio de agentes de IA especializados (arquiteto, gerente de projeto, desenvolvedor, revisor, etc.), seguindo o pipeline documentado em `CLAUDE.md`. O registro rastreável de prompts relevantes e revisões está em [`spec/prompts.md`](./spec/prompts.md) e será atualizado incrementalmente durante a implementação — não reconstituído no final.

## Entregáveis do case

- [x] Repositório público no GitHub
- [x] Spec técnica (`spec/`)
- [ ] README completo *(este arquivo — será atualizado conforme a implementação avança)*
- [ ] Registro de prompts de IA consolidado
- [ ] Implementação (`api/`, `web/`)
- [ ] Testes automatizados
- [ ] Vídeo de arquitetura e demonstração
- [ ] Link de deploy *(opcional — só se sobrar tempo, ver `spec/product.md`)*
