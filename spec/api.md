Todas as rotas (exceto `auth/register` e `auth/login`) exigem cookie de sessão válido — `401` caso ausente/expirado. Todo recurso de `Project`/`Task`/`Attachment` é escopado ao usuário autenticado — acessar recurso de outro usuário retorna `404`.

Prefixo base: `/api/v1`

---

## POST /auth/register

**Description:** Cria uma nova conta de usuário.

**Request:**
```json
{ "email": "user@example.com", "password": "senha-forte-123" }
```

**Response:** `201`
```json
{ "id": "uuid", "email": "user@example.com" }
```

**Errors:**
- 400: e-mail em formato inválido ou senha abaixo do mínimo de segurança
- 409: e-mail já cadastrado

---

## POST /auth/login

**Description:** Autentica o usuário e define o cookie `httpOnly` de sessão (JWT).

**Request:**
```json
{ "email": "user@example.com", "password": "senha-forte-123" }
```

**Response:** `200`
```json
{ "id": "uuid", "email": "user@example.com" }
```

**Errors:**
- 401: credenciais inválidas

---

## POST /auth/logout

**Description:** Invalida a sessão atual, limpando o cookie.

**Response:** `204` (sem corpo)

---

## GET /auth/me

**Description:** Retorna o usuário autenticado — usado pelo frontend para checar sessão persistente ao carregar a aplicação.

**Response:** `200`
```json
{ "id": "uuid", "email": "user@example.com" }
```

**Errors:**
- 401: sem sessão válida

---

## GET /projects

**Description:** Lista os projetos do usuário autenticado.

**Response:** `200`
```json
[{ "id": "uuid", "name": "Website redesign", "created_at": "2026-07-01T10:00:00Z" }]
```

---

## POST /projects

**Description:** Cria um novo projeto.

**Request:**
```json
{ "name": "Website redesign" }
```

**Response:** `201`
```json
{ "id": "uuid", "name": "Website redesign", "created_at": "2026-07-01T10:00:00Z" }
```

**Errors:**
- 400: nome vazio

---

## GET /projects/{project_id}

**Description:** Detalhe de um projeto.

**Response:** `200`
```json
{ "id": "uuid", "name": "Website redesign", "created_at": "2026-07-01T10:00:00Z" }
```

**Errors:**
- 404: projeto não existe ou não pertence ao usuário

---

## PATCH /projects/{project_id}

**Description:** Atualiza o nome do projeto.

**Request:**
```json
{ "name": "Novo nome" }
```

**Response:** `200` — projeto atualizado

**Errors:**
- 400: nome vazio
- 404: projeto não existe ou não pertence ao usuário

---

## DELETE /projects/{project_id}

**Description:** Remove o projeto e suas tarefas (cascade).

**Response:** `204`

**Errors:**
- 404: projeto não existe ou não pertence ao usuário

---

## GET /projects/{project_id}/tasks

**Description:** Lista as tarefas de um projeto. Suporta filtros opcionais via query params (ver `spec/product.md` — "Improvement Suggestions").

**Query params:**
- `status` (opcional): filtra por um dos 4 status
- `tag` (opcional): filtra tarefas que contêm a tag informada

**Response:** `200`
```json
[{
  "id": "uuid",
  "title": "Redesenhar tela de login",
  "short_description": "Criar nova proposta de UI para autenticação",
  "due_date": "2026-06-28T18:00:00Z",
  "status": "in_progress",
  "tags": ["design"]
}]
```

**Errors:**
- 404: projeto não existe ou não pertence ao usuário

---

## POST /projects/{project_id}/tasks

**Description:** Cria uma tarefa no projeto.

**Request:**
```json
{
  "title": "Redesenhar tela de login",
  "short_description": "Criar nova proposta de UI para autenticação",
  "full_description": "Levantar referências e propor 2 variações...",
  "due_date": "2026-06-28T18:00:00Z",
  "tags": ["design"]
}
```

**Response:** `201` — tarefa criada com `status: "not_started"`

**Errors:**
- 400: título ausente
- 404: projeto não existe ou não pertence ao usuário

---

## GET /tasks/{task_id}

**Description:** Detalhe completo de uma tarefa (inclui `full_description` e anexos).

**Response:** `200`

**Errors:**
- 404: tarefa não existe ou não pertence ao usuário

---

## PATCH /tasks/{task_id}

**Description:** Atualiza qualquer campo da tarefa — incluindo `status` (usado tanto pelo formulário de edição quanto pelo controle de status no card do kanban, ver `ADR-004`; sem drag-and-drop, sem campo de posição).

**Request (exemplo — mudança de status via kanban):**
```json
{ "status": "done" }
```

**Response:** `200` — tarefa atualizada

**Errors:**
- 400: valor de `status` inválido, ou campo obrigatório removido (ex: `title` vazio)
- 404: tarefa não existe ou não pertence ao usuário

---

## DELETE /tasks/{task_id}

**Description:** Remove a tarefa e seus anexos (cascade).

**Response:** `204`

**Errors:**
- 404: tarefa não existe ou não pertence ao usuário

---

## POST /tasks/{task_id}/attachments

**Description:** Upload de um anexo/foto para a tarefa (`multipart/form-data`).

**Request:** `multipart/form-data` com campo `file`

**Response:** `201`
```json
{
  "id": "uuid",
  "filename": "mockup.png",
  "content_type": "image/png",
  "size_bytes": 245678,
  "url": "/api/v1/attachments/uuid/download"
}
```

**Errors:**
- 400: arquivo ausente, tipo não permitido, ou acima do limite de tamanho
- 404: tarefa não existe ou não pertence ao usuário

---

## GET /tasks/{task_id}/attachments

**Description:** Lista os anexos de uma tarefa.

**Response:** `200` — array de anexos (mesmo formato do POST)

---

## GET /attachments/{attachment_id}/download

**Description:** Serve o arquivo do anexo.

**Response:** `200` — binário do arquivo com `Content-Type` correto

**Errors:**
- 404: anexo não existe ou a tarefa associada não pertence ao usuário

---

## DELETE /attachments/{attachment_id}

**Description:** Remove um anexo.

**Response:** `204`

**Errors:**
- 404: anexo não existe ou a tarefa associada não pertence ao usuário

---

## POST /assistant/chat

**Description:** Extensão (além do escopo mínimo). Envia uma mensagem em linguagem natural ao assistente, que pode consultar/criar/atualizar tarefas e projetos do usuário autenticado via tool use (Claude). Roda no mesmo processo da API — sem servidor MCP externo. Ver `spec/tools.md` e `spec/prompts.md`.

**Request:**
```json
{
  "message": "cria uma tarefa 'revisar contrato' no projeto Website redesign para sexta",
  "conversation_id": "uuid-ou-null"
}
```

**Response:** `200`
```json
{
  "conversation_id": "uuid",
  "reply": "Criei a tarefa \"revisar contrato\" no projeto Website redesign, com prazo para sexta-feira.",
  "tool_calls": [
    { "tool": "create_task", "input": { "project_id": "uuid", "title": "revisar contrato", "due_date": "2026-07-03T18:00:00Z" } }
  ]
}
```

`tool_calls` é retornado para a UI poder exibir de forma transparente o que o assistente executou de fato (nunca esconder a ação do usuário).

**Errors:**
- 400: mensagem vazia
- 401: sem sessão válida
- 502: falha ao chamar a API da Anthropic (timeout, rate limit, etc.)
