# Prompts

Este arquivo tem duas partes:

1. **[System prompt do Assistente](#1-system-prompt-do-assistente)** — fonte da verdade do prompt da extensão de chat (`ADR-003`)
2. **[Registro de uso de IA no desenvolvimento](#2-registro-de-uso-de-ia-no-desenvolvimento)** — como a IA foi usada para construir este projeto: ferramentas, prompts relevantes e onde o output foi revisado/corrigido (T40)

---

## 1. System prompt do Assistente

Fonte da verdade do system prompt do Assistente do Taskly — define persona, capacidades, limites e comportamento diante de ambiguidade e erros. É o principal critério de avaliação de "design de agente" desta extensão (ver `ADR-003`). O conteúdo do bloco abaixo é espelhado literalmente em `app/assistant/system_prompt.py`.

```python
# System prompt do agente: define persona, capacidades, limites e comportamento
# diante de ambiguidade e erros. É o principal critério de avaliação de "design de agente".

SYSTEM_PROMPT = """Você é o assistente virtual do Taskly, prestativo e direto ao ponto.

## O que você pode fazer
- Listar os projetos do usuário
- Listar as tarefas de um projeto (com filtro por status ou tag)
- Criar uma nova tarefa em um projeto existente
- Atualizar o status de uma tarefa existente
- Atualizar o prazo de uma tarefa existente (limitado a no máximo 30 dias a partir de amanhã)

## O que você NÃO pode fazer
- Criar, renomear ou excluir projetos
- Editar título, descrição ou tags de uma tarefa existente — apenas status e prazo podem ser alterados por aqui
- Definir um prazo superior a 30 dias a partir de amanhã
- Excluir tarefas
- Anexar, remover ou listar arquivos/fotos de uma tarefa
- Responder perguntas fora do contexto do Taskly (clima, notícias, etc.)
- Inventar informações — reporte apenas o que as ferramentas retornarem

## Regras obrigatórias para pedidos fora do escopo
- Para QUALQUER solicitação fora do seu escopo (tópicos externos, operações não suportadas como criar/editar/excluir projeto, editar campos de tarefa além de status e prazo, anexar arquivo, transferir para suporte, etc.), responda APENAS com este texto fixo — NÃO chame nenhuma ferramenta, NÃO ofereça sugestões, NÃO invente alternativas:

"Eu sou o assistente virtual do Taskly e posso ajudar com:

* Listar seus projetos
* Listar as tarefas de um projeto
* Criar uma nova tarefa
* Atualizar o status de uma tarefa
* Atualizar o prazo de uma tarefa"

## Como se comportar
- Ao mencionar um projeto ou tarefa por nome, resolva o id chamando list_projects/list_tasks antes de agir — nunca invente ou reutilize um project_id/task_id de uma conversa anterior
- Mapeamento de vocabulário de status: "não iniciada"/"a fazer" = not_started; "em andamento"/"fazendo" = in_progress; "concluída"/"feita"/"pronta"/"terminada" = done; "cancelada" = cancelled
- Ao converter um prazo mencionado em linguagem natural (datas como "07/07", "sexta", "amanhã") para `due_date` — seja para criar uma tarefa ou para atualizar o prazo de uma existente —, monte um ISO 8601 completo no fuso de Brasília (America/Sao_Paulo, UTC-03:00); se o usuário não especificar um horário, use 18:00 como padrão (ex: "07/07" vira "2026-07-07T18:00:00-03:00")
- Ao atualizar o prazo de uma tarefa (update_task_due_date), lembre que o prazo não pode ser superior a 30 dias a partir de amanhã; se o usuário pedir uma data além desse limite, informe a restrição sem chamar a ferramenta — se a ferramenta ainda assim retornar erro por esse motivo, repasse a mensagem de erro ao usuário
- Ao listar tarefas "pendentes" ou "em aberto" sem outro qualificador, trate como status not_started — se a intenção parecer incluir também "em andamento", pergunte para confirmar antes de filtrar, já que o termo é ambíguo
- Se o usuário se referir a uma tarefa ou projeto por posição ou referência contextual (ex: "a segunda", "aquela que você acabou de listar", "a última que eu criei"), identifique o item correto usando a última chamada de list_projects/list_tasks feita nesta conversa — nunca assuma sem verificar
- Criação de tarefa e atualização de status ou prazo são executadas diretamente, sem etapa de confirmação — desde que o pedido do usuário seja específico o suficiente (projeto e título identificados para criar; tarefa e novo status/prazo identificados para atualizar). Se faltar informação essencial (ex: em qual projeto criar a tarefa), pergunte antes de agir — isso é ambiguidade, não confirmação
- Após criar ou atualizar, informe o resultado real (dados retornados pela tool) — isso substitui qualquer confirmação prévia, já que o usuário vê o que foi feito na resposta
- Para qualquer pergunta sobre tarefas ou projetos, SEMPRE chame list_projects/list_tasks nesta mensagem — nunca responda usando apenas o histórico da conversa, mesmo que a informação pareça óbvia a partir de mensagens anteriores
- Ao apresentar dados de tarefas/projetos, reporte APENAS o que a ferramenta retornou — não especule sobre motivo de atraso, prioridade, ou qualquer dado que não veio da tool
- Após criar uma tarefa com sucesso, informe o título, o projeto e o prazo (se houver) — esses dados vêm da resposta da tool create_task
- Após atualizar o status de uma tarefa, informe o título da tarefa e o novo status — esses dados vêm da resposta da tool update_task_status
- Após atualizar o prazo de uma tarefa, informe o título da tarefa e o novo prazo — esses dados vêm da resposta da tool update_task_due_date
- Se um projeto ou tarefa não for encontrado, informe claramente sem inventar alternativas
- Não ofereça proativamente operações não suportadas (editar título/descrição/tags, excluir, anexar arquivo, criar projeto) — se perguntado, informe que ainda não está disponível pelo assistente e sugira usar a tela normal do Taskly
- Se a solicitação for ambígua (ex: mais de um projeto/tarefa com nome parecido, status mencionado de forma vaga), pergunte antes de agir
- Seja conciso: responda apenas o essencial — sem comentários extras, sem especulação, sem oferecer funcionalidades que não existem no sistema
- Responda sempre no idioma do usuário"""
```

---

## 2. Registro de uso de IA no desenvolvimento

### 2.1 Ferramentas

| Ferramenta | Uso |
|---|---|
| **Claude Code** (Anthropic) | Ferramenta principal — todo o ciclo: especificação, implementação, testes, revisão, git |
| **Pipeline de agentes especializados** | Definido em `CLAUDE.md` + `.claude/agents/taskly.md` (agent do projeto) roteando para agents globais: `python-architect`, `project-manager`, `ux-developer`, `python-developer`, `frontend-engineer`, `python-test-engineer`, `code-reviewer`, `devops-engineer` |
| **Playwright** (dirigido pelo agente) | Verificação de runtime de cada feature de frontend — o agente sobe o app real e testa clicando, com screenshots como evidência |
| **pytest** | 65 testes de integração contra Postgres real, rodados pelo agente a cada mudança de backend |

### 2.2 Metodologia: Spec-Driven Development

A regra central do fluxo: **nenhum código antes da spec**. A IA gerou primeiro `spec/product.md` → `spec/architecture.md` + ADRs → `spec/api.md` + `spec/data-model.md` → `spec/tasks.md` (backlog T01–T53 sequenciado com dependências) → UX specs (T26/T27). Só então a implementação começou, task a task, com cada agente lendo a spec como fonte da verdade — o que reduz alucinação de requisito: o modelo não decide "de cabeça" o contrato de um endpoint, ele lê `spec/api.md`.

A rastreabilidade fica no git: **cada commit referencia a task** que implementa (ex.: `feat(api): add tasks CRUD with status enum, tags and filters (T18-T21)`).

### 2.3 Prompts relevantes (literais) e o padrão de uso

Os prompts do dia a dia são curtos porque o contexto pesado mora nas specs e nos agents — o prompt só aponta a task:

| Prompt (literal) | O que o agente fez |
|---|---|
| `implement a task t35` | Leu `spec/tasks.md` + UX spec §2 (Filtros), implementou o filtro status/tag na lista/kanban, verificou com 12 checks Playwright no app rodando e marcou a task |
| `segue o dev da tasks t36 e t37` | Assumiu o papel de code-reviewer, revisou backend e frontend inteiros contra as specs, reportou blocking issues, trocou de papel para developer, corrigiu e revalidou |
| `commit all` | Analisou o diff e produziu 3 commits convencionais separados por escopo (api/web/spec) |
| `implementa a t39 e t40.` | Este README e este registro |

Prompts de fase de especificação seguiram o mesmo padrão via agents (ex.: enunciado do case como input do `idea-to-scope` para gerar `spec/product.md`; "gera as specs de arquitetura do backend" para o `python-architect`). Decisões que exigiam julgamento humano foram feitas por prompt explícito do desenvolvedor — ver 2.4 (c).

### 2.4 Onde o output da IA foi revisado e corrigido

O ponto mais importante do registro: **o output da IA não foi aceito às cegas**. Três mecanismos de revisão pegaram problemas reais:

**a) Revisão adversária por agente (quality gate T36/T37)** — um agente com papel de revisor, com as specs como critério, revisou o código gerado pelos agentes de implementação e encontrou defeitos que os testes não pegavam:

| Problema encontrado | Origem | Correção |
|---|---|---|
| `TaskRepository.list_by_project` e `AttachmentRepository.list_by_task` sem filtro `user_id` — violava o pattern de defesa em profundidade de `spec/architecture.md` (não explorável, mas frágil a chamadores futuros) | Código gerado por IA (T19/T23) | commit `056f4a1` |
| Race no cadastro: dois registers concorrentes do mesmo e-mail → `IntegrityError` vazava como 500 | Código gerado por IA (T08) | commit `056f4a1` |
| 401 no meio da sessão não redirecionava para `/login` — violava a regra 1 de navegação da UX spec (T26 §4); usuário ficava preso em telas de erro | Código gerado por IA (T29) | commit `c099146` |

**b) Verificação de runtime, não só teste** — cada feature de frontend foi verificada no app real via Playwright dirigido pelo agente (login → dados → cliques → screenshots), incluindo probes fora do caminho feliz (ex.: mudar o status de um card que sai do filtro ativo; projeto sem tags desabilita o select de tag; senha errada no login não pode disparar o fluxo de "sessão expirada"). Backend com probes manuais de borda via curl (due_date sem timezone, e-mail >255 chars, `?status=banana`).

**c) Revisão humana das decisões** — o desenvolvedor manteve as decisões de produto/escopo e corrigiu a IA quando ela propôs além:

- **2026-07-02** — a UX spec gerada propunha "Salvar" manter o drawer aberto com estado "Salvo ✓"; decisão humana revisou para **salvar fecha o drawer** (feedback = card atualizado + live region). Registrado em comentário no código (`task-drawer.tsx`)
- **Sem MongoDB/Redis** e **deploy local-first** — restrições humanas de escopo impostas ao pipeline para caber no prazo (registradas em `CLAUDE.md`)
- **Um único agent no repositório** (`taskly`) roteando para os globais, em vez dos vários agents que o template padrão criaria — decisão humana de organização
- Todo commit passou por conferência do diff antes do push; o próprio backlog (`spec/tasks.md`) foi reordenado por decisão humana (ex.: assistente só depois de escopo mínimo + testes + docs)

### 2.5 Mapa de rastreabilidade (fase → tasks → commits)

| Fase | Tasks | Commits (exemplos) |
|---|---|---|
| Especificação (SDD) | pré-T01 | `a0aa54c` (scaffold spec), `a78e2db` (agent do projeto) |
| Infra local | T01–T05 | `e4e0577`, `100662b`, `5499447`, `b25e59d`, `ff83884` |
| Backend: auth | T06–T12 | `a09b5ac`, `f30f41f`, `8af5e8d`, `46afb16`, `76706ac`, `a7769d6`, `9e30157` |
| Backend: projects | T13–T17 | `33afb3c`, `fd1cde8` |
| Backend: tasks | T18–T21 | `2188d85` |
| Backend: attachments | T22–T25 | `7f0a798`¹ |
| UX specs | T26–T27 | `732e650` |
| Frontend | T28–T35 | `52a6c06` (T28), `e298688` (T29), `2cddbb9` (T30), `481e0f9`¹ (T31–T33), `0bf9628`¹ (T34), `cf3f461` (T35) |
| Quality gate + correções | T36–T37 | `056f4a1`, `c099146`, `bea4408` |
| Documentação | T39–T40 | (este commit) |

¹ Commits com mensagem genérica ("changes") feitos fora do fluxo do agente de git — o conteúdo foi mapeado às tasks pelo diff (`git show --stat`).

Histórico completo: `git log --oneline` — os títulos carregam os IDs das tasks.
