# ADR-002: Armazenamento de tags da tarefa (array nativo vs tabela relacional)

**Date:** 2026-07-01
**Status:** Accepted
**Deciders:** Usuário (dono do projeto) + python-architect

---

## Context

O case exige que cada tarefa tenha "tags" como campo editável. Não há requisito de autocomplete, reuso de tag entre tarefas, nem gestão centralizada de tags (criar/renomear/excluir tag como entidade). Prazo de 3 dias.

---

## Decision

Tags serão armazenadas como coluna `text[]` (array nativo do PostgreSQL) diretamente na tabela `Task` — sem tabela `Tag` separada.

---

## Options Considered

### Option 1: Coluna `text[]` na própria Task (escolhida)

**Pros:**
- Zero tabelas/joins extras — leitura e escrita da tarefa já trazem as tags
- Suficiente para o filtro por tag pedido em "Improvement Suggestions" (`WHERE tag = ANY(tags)`)
- Rápido de implementar em 3 dias

**Cons:**
- Sem autocomplete de tags já usadas sem uma query `SELECT DISTINCT unnest(tags)`
- Sem unicidade/normalização (usuário pode digitar "Design" e "design" como tags diferentes)

### Option 2: Tabela `Tag` + tabela associativa `task_tags` (many-to-many)

**Pros:**
- Permite autocomplete, renomear tag em um lugar só, evitar duplicatas
- Mais "correto" normativamente

**Cons:**
- Duas tabelas e joins extras para uma funcionalidade que o case não pede explicitamente
- Custo de implementação não se paga dentro do prazo de 3 dias para o ganho que traz

---

## Rationale

O case não pede gestão de tags como entidade — só que a tarefa tenha tags editáveis. A Option 1 entrega isso e ainda viabiliza filtro por tag (sugestão de valor already presente em `spec/product.md`) sem o custo de uma modelagem many-to-many que nada no escopo justifica agora.

---

## Consequences

**Positive:**
- Menos código, menos migrations, menos superfície de teste
- Filtro por tag funciona nativamente com operadores de array do Postgres

**Negative / Trade-offs:**
- Sem normalização — duas grafias da "mesma" tag são tratadas como diferentes
- Se o produto crescesse além do case, migrar para Option 2 exigiria um script de backfill

**Risks:**
- Baixo — o volume de dados de um case de avaliação não expõe os limites de performance de arrays no Postgres.

---

## Implementation Notes

- Campo `tags: List[str]` no schema Pydantic, mapeado para `ARRAY(String)` no SQLAlchemy
- Normalizar para lowercase e `strip()` no `service` antes de persistir, para reduzir duplicatas óbvias (ex: `"Design"` → `"design"`), sem impedir o usuário de usar qualquer string
