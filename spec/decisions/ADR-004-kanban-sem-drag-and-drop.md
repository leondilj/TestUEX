# ADR-004: Kanban sem drag-and-drop — mudança de status via ação explícita

**Date:** 2026-07-01
**Status:** Accepted
**Deciders:** Usuário (dono do projeto) + python-architect

---

## Context

O case pede apenas: "Visualização em lista e kanban — o usuário pode alternar entre as duas visões por meio de um botão de toggle" e "Status das tarefas... atualizável pelo usuário a qualquer momento" (`UEX Teste Técnico Vaga Dev Fullstack.md`). O mock de referência do enunciado só mostra a visão em lista — o layout do kanban e o mecanismo de mudança de status são decisão livre do time. A modelagem original (`spec/data-model.md`) já incluía um campo `Task.position` para suportar reordenação por drag-and-drop, o que introduziu um problema em aberto no backlog (`spec/tasks.md`, item T17): como reindexar `position` de todas as tarefas afetadas quando uma é movida. O usuário decidiu, para simplificar dentro do prazo de 3 dias, **não implementar drag-and-drop neste momento**.

---

## Decision

O kanban muda de status por **ação explícita** (botão/dropdown por tarefa, tanto na lista quanto no kanban) que chama `PATCH /tasks/{id}` com `{ "status": "..." }` — sem campo `position`, sem reordenação manual, sem drag-and-drop. O agrupamento das colunas do kanban é feito apenas por `status`; a ordem das tarefas dentro de uma coluna/lista é sempre por `created_at` (mais antiga primeiro), sem controle manual do usuário.

---

## Options Considered

### Option 1: Sem `position`, mudança de status via botão/dropdown (escolhida)

Kanban só agrupa por `status`. Ordem fixa por `created_at`. Mudar o status de uma tarefa é a única ação suportada — feita por um controle explícito (ex: dropdown de status no card), não por arrastar o card entre colunas.

**Pros:**
- Atende literalmente o requisito do case ("status atualizável a qualquer momento") sem a complexidade de reindexação
- Remove um campo, uma migration e uma regra de reindexação do escopo — menos superfície de bug e de teste
- `PATCH /tasks/{id}` fica mais simples: só `status` muda por essa via, igual a qualquer outro campo da tarefa

**Cons:**
- UX menos "kanban clássico" — usuário não arrasta cards, só escolhe status num controle
- Se o usuário quiser reordenar manualmente dentro de uma coluna (não pedido pelo case), não há suporte

### Option 2: Manter `position`, implementar drag-and-drop com reindexação completa por coluna

Mantém o plano original: `position` por tarefa, reindexado a cada `PATCH` que move uma tarefa (T17 do backlog).

**Pros:**
- UX mais familiar de ferramentas de kanban (Trello-like)

**Cons:**
- Exige definir e implementar lógica de reindexação (transação que reescreve `position` de várias tarefas), migration extra, e testes de concorrência/edge case
- Não é requisito explícito do case — custo não se paga dentro do prazo de 3 dias
- Já havia gerado um bloqueio de arquitetura em aberto (T17) sem necessidade real

---

## Rationale

O case não pede drag-and-drop, só o toggle lista/kanban e a atualização de status "a qualquer momento" — um dropdown/botão de status atende isso com uma fração do custo de implementação e teste. O usuário confirmou explicitamente que não quer perseguir drag-and-drop agora. Reduzir escopo aqui libera tempo para o que **é** avaliado explicitamente (funcionalidade completa, testes, documentação) sem abrir mão de nenhum requisito do enunciado.

---

## Consequences

**Positive:**
- Menos um campo no modelo de dados, uma migration a menos, um endpoint mais simples
- Remove o bloqueio de arquitetura T17 do backlog — desbloqueia o backend de tasks imediatamente
- Frontend do kanban fica mais simples de implementar e testar (sem biblioteca de drag-and-drop, sem estado otimista de reordenação)

**Negative / Trade-offs:**
- UX do kanban é mais simples que o "clássico" — aceito conscientemente pelo usuário
- Se o produto evoluir além do case, adicionar reordenação manual exigiria reintroduzir um campo de ordenação (ex: `position` ou `sort_key`) e migração de dados — não é um problema agora

**Risks:**
- Baixo — nenhuma migration já foi aplicada em produção; a mudança é só de spec, antes de qualquer código ser escrito.

---

## Implementation Notes

- Remover `position` de `spec/data-model.md` (`Task`) — feito nesta revisão
- Remover menções a `position`/reordenação de `spec/api.md` (`GET/POST /projects/{id}/tasks`, `PATCH /tasks/{id}`) — feito nesta revisão
- `task_repository.list_by_project` ordena por `created_at ASC` por padrão — sem parâmetro de reordenação
- Frontend: card de tarefa (lista e kanban) tem um controle de status (ex: `<select>` ou menu) que chama `PATCH /tasks/{id}` — nenhuma biblioteca de drag-and-drop é necessária
- Se o usuário quiser reordenação manual no futuro, é uma nova ADR — não reabrir esta decisão sem uma necessidade explícita

---

## References

- `UEX Teste Técnico Vaga Dev Fullstack.md` — requisito original (toggle lista/kanban, status atualizável)
- `spec/data-model.md` — modelo de `Task` sem `position`
- `spec/api.md` — contrato de `PATCH /tasks/{id}` sem `position`
- `spec/tasks.md` — item T17 removido/resolvido por esta decisão
