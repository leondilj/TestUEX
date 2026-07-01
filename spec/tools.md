Ferramentas do assistente (extensão, além do escopo mínimo). Rodam **dentro do processo da API** — cada função chama diretamente o `service` correspondente (mesma camada usada pelos routers REST), sempre escopada ao `user_id` do usuário autenticado na requisição de chat. Nenhuma ferramenta acessa outro usuário além de quem está logado.

---

## Tool: list_projects

**Description:** Lista os projetos do usuário autenticado.
**Trigger:** o usuário pergunta quais projetos existem, ou o assistente precisa resolver o `project_id` a partir de um nome de projeto mencionado em linguagem natural (ex: "no projeto Website redesign").

**Input:**
_(nenhum parâmetro — sempre escopado ao usuário da sessão)_

**Output:**
```json
[{ "id": "uuid", "name": "Website redesign" }]
```

**Example:**
Usuário: "quais projetos eu tenho?" → assistente chama `list_projects`, responde com a lista em texto.

---

## Tool: list_tasks

**Description:** Lista as tarefas de um projeto, com filtro opcional por status ou tag.
**Trigger:** o usuário pergunta sobre tarefas pendentes, o status de um projeto, ou precisa que o assistente resolva um `task_id` a partir de um título mencionado (ex: "marca a tarefa de revisar contrato como concluída").

**Input:**
- `project_id` (string, required): UUID do projeto — resolvido previamente via `list_projects` se o usuário só mencionou o nome
- `status` (string, optional): um de `not_started`, `in_progress`, `done`, `cancelled`
- `tag` (string, optional)

**Output:**
```json
[{ "id": "uuid", "title": "Revisar contrato", "status": "not_started", "due_date": "2026-07-03T18:00:00Z", "tags": ["financeiro"] }]
```

**Example:**
Usuário: "o que está pendente no projeto Website redesign?" → assistente chama `list_projects` (se ainda não souber o id), depois `list_tasks(project_id=..., status="not_started")`.

---

## Tool: create_task

**Description:** Cria uma nova tarefa em um projeto existente.
**Trigger:** o usuário pede explicitamente para criar/adicionar uma tarefa.

**Input:**
- `project_id` (string, required) — nunca inventado; deve vir de um `list_projects` prévio na mesma conversa
- `title` (string, required)
- `short_description` (string, optional)
- `full_description` (string, optional)
- `due_date` (string, ISO 8601, optional)
- `tags` (array de string, optional)

**Output:**
```json
{ "id": "uuid", "title": "Revisar contrato", "status": "not_started", "due_date": "2026-07-03T18:00:00Z" }
```

**Example:**
Usuário: "cria uma tarefa 'revisar contrato' no projeto Website redesign para sexta" → assistente resolve `project_id` via `list_projects`, converte "sexta" para uma data ISO explícita, chama `create_task`.

---

## Tool: update_task_status

**Description:** Atualiza o status de uma tarefa existente.
**Trigger:** o usuário diz que iniciou, concluiu ou cancelou uma tarefa.

**Input:**
- `task_id` (string, required) — nunca inventado; deve vir de um `list_tasks` prévio na mesma conversa
- `status` (string, required): um de `not_started`, `in_progress`, `done`, `cancelled`

**Output:**
```json
{ "id": "uuid", "title": "Revisar contrato", "status": "done" }
```

**Example:**
Usuário: "marca a tarefa de revisar contrato como concluída" → assistente resolve `task_id` via `list_tasks` (buscando pelo título mencionado), chama `update_task_status(task_id=..., status="done")`.

---

## Regra transversal — resolução de IDs

Nenhuma tool que recebe `project_id` ou `task_id` deve ser chamada com um ID que o modelo não obteve de uma chamada anterior a `list_projects`/`list_tasks` **na mesma conversa**. Se o usuário mencionar um projeto/tarefa por nome (ou por referência posicional/contextual, ex: "a segunda", "aquela que você mostrou") e o assistente ainda não tiver essa lista carregada nesta conversa, a primeira ação deve ser sempre listar antes de agir. Ver `spec/prompts.md` — system prompt completo, seção "Como se comportar".
