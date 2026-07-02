// Tipos espelhando spec/data-model.md e as respostas de spec/api.md.
// Datas trafegam como string ISO 8601 (UTC) — conversão para Date é
// responsabilidade de quem exibe, nunca do api-client.

export interface User {
  id: string;
  email: string;
}

export interface Project {
  id: string;
  name: string;
  created_at: string;
}

export const TASK_STATUSES = [
  "not_started",
  "in_progress",
  "done",
  "cancelled",
] as const;

export type TaskStatus = (typeof TASK_STATUSES)[number];

// Rótulos pt-BR definidos em ux-spec-navigation-and-identity.md §3
export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  not_started: "Não iniciada",
  in_progress: "Em andamento",
  done: "Concluída",
  cancelled: "Cancelada",
};

// Item de GET /projects/{id}/tasks — sem full_description nem anexos
export interface TaskSummary {
  id: string;
  title: string;
  short_description: string | null;
  due_date: string | null;
  status: TaskStatus;
  tags: string[];
  created_at: string;
}

// Detalhe completo de GET /tasks/{id}
export interface Task extends TaskSummary {
  project_id: string;
  full_description: string | null;
  updated_at: string;
  attachments: Attachment[];
}

export interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  url: string;
}

// ---- Payloads de requisição ----

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface ProjectInput {
  name: string;
}

export interface TaskCreateInput {
  title: string;
  short_description?: string | null;
  full_description?: string | null;
  due_date?: string | null;
  tags?: string[];
}

// PATCH parcial — enviar somente os campos alterados; `null` limpa o campo
// (ver ux-spec-task-views-and-form.md §3), `status` cobre o controle do card
export interface TaskUpdateInput extends Partial<TaskCreateInput> {
  status?: TaskStatus;
}

export interface TaskFilters {
  status?: TaskStatus;
  tag?: string;
}

// ---- Extensão: assistente (POST /assistant/chat, além do escopo mínimo) ----

export interface AssistantToolCall {
  tool: string;
  input: Record<string, unknown>;
}

export interface AssistantChatRequest {
  message: string;
  conversation_id: string | null;
}

export interface AssistantChatResponse {
  conversation_id: string;
  reply: string;
  tool_calls: AssistantToolCall[];
}
