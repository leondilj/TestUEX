## User

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária |
| email | string | yes | Único, usado como login |
| password_hash | string | yes | Hash bcrypt — nunca a senha em texto puro |
| created_at | datetime | yes | Timestamp de criação |
| updated_at | datetime | yes | Timestamp da última atualização |

**Relationships:**
- `User` has many `Project` via `project.user_id`

---

## Project

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária |
| user_id | UUID (FK → User) | yes | Dono do projeto |
| name | string | yes | Nome do projeto |
| created_at | datetime | yes | Timestamp de criação |
| updated_at | datetime | yes | Timestamp da última atualização |

**Relationships:**
- `Project` belongs to `User` via `user_id`
- `Project` has many `Task` via `task.project_id`

---

## Task

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária |
| project_id | UUID (FK → Project) | yes | Projeto ao qual a tarefa pertence |
| title | string | yes | Título da tarefa |
| short_description | string (≤ 280 chars) | no | Descrição curta, exibida na lista/kanban |
| full_description | text | no | Descrição completa |
| due_date | datetime (timezone-aware) | no | Prazo (data e hora) |
| status | enum: `not_started`, `in_progress`, `done`, `cancelled` | yes | Default `not_started` |
| tags | array de string (`text[]`) | no | Ver `ADR-002` em `spec/architecture.md` |
| created_at | datetime | yes | Timestamp de criação — também usado para ordenar a lista/kanban (mais antiga primeiro). Ver `ADR-004`: sem drag-and-drop, sem campo de posição manual. |
| updated_at | datetime | yes | Timestamp da última atualização |

**Relationships:**
- `Task` belongs to `Project` via `project_id`
- `Task` has many `Attachment` via `attachment.task_id`

**Constraints:**
- Todo campo é editável após a criação (requisito explícito do case) — exceto `id`, `created_at`.
- `status` só aceita os 4 valores do enum — validado no schema Pydantic e reforçado como `CHECK` constraint no banco.

---

## Attachment

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária |
| task_id | UUID (FK → Task) | yes | Tarefa à qual o anexo pertence |
| filename | string | yes | Nome original do arquivo |
| content_type | string | yes | MIME type (ex: `image/png`, `application/pdf`) |
| size_bytes | integer | yes | Tamanho do arquivo em bytes |
| storage_path | string | yes | Caminho relativo em `uploads/{task_id}/{filename}` |
| created_at | datetime | yes | Timestamp de upload |

**Relationships:**
- `Attachment` belongs to `Task` via `task_id`

**Open question (herdada de `spec/product.md`):** limite de tamanho/tipo de arquivo aceito ainda não definido — recomendação: começar com limite de 10MB por arquivo e tipos comuns (imagem, PDF, doc), configurável via `config.py`, e revisar se sobrar tempo.

---

## AssistantConversation

_(Extensão, além do escopo mínimo — ver `ADR-003`, nota de complemento)_

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária — mesmo valor usado como `conversation_id` na API |
| user_id | UUID (FK → User) | yes | Dono da conversa — nunca acessível por outro usuário |
| created_at | datetime | yes | Timestamp de criação |
| updated_at | datetime | yes | Timestamp da última mensagem |

**Relationships:**
- `AssistantConversation` belongs to `User` via `user_id`
- `AssistantConversation` has many `AssistantMessage` via `assistant_message.conversation_id`

---

## AssistantMessage

_(Extensão, além do escopo mínimo — ver `ADR-003`, nota de complemento)_

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | Chave primária |
| conversation_id | UUID (FK → AssistantConversation) | yes | Conversa à qual a mensagem pertence |
| role | enum: `user`, `assistant` | yes | Quem enviou a mensagem |
| content | text | yes | Conteúdo em texto da mensagem (a resposta final, não os tool calls intermediários) |
| created_at | datetime | yes | Timestamp de envio — usado para reconstruir a ordem do histórico |

**Relationships:**
- `AssistantMessage` belongs to `AssistantConversation` via `conversation_id`

**Constraints:**
- `tool_calls` executados em cada turno não são persistidos como entidade própria — são recalculados/retornados apenas na resposta HTTP daquele turno (ver `spec/api.md`), já que o histórico reenviado ao modelo usa só `role`+`content`.
