// Wrapper de fetch para a API do Taskly (spec/api.md).
// Sessão via cookie httpOnly (ADR-001): todo request sai com
// credentials: "include" — nunca header Authorization.

import type {
  AssistantChatRequest,
  AssistantChatResponse,
  Attachment,
  AuthCredentials,
  Project,
  ProjectInput,
  Task,
  TaskCreateInput,
  TaskFilters,
  TaskSummary,
  TaskUpdateInput,
  User,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    // corpo de erro do FastAPI: { detail: string | object }
    public readonly detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    ...init,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? null);
  }

  // 204 (logout, deletes) não tem corpo
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  auth: {
    register: (credentials: AuthCredentials) =>
      apiFetch<User>("/auth/register", jsonInit("POST", credentials)),
    login: (credentials: AuthCredentials) =>
      apiFetch<User>("/auth/login", jsonInit("POST", credentials)),
    logout: () => apiFetch<void>("/auth/logout", { method: "POST" }),
    me: () => apiFetch<User>("/auth/me"),
  },

  projects: {
    list: () => apiFetch<Project[]>("/projects"),
    create: (input: ProjectInput) =>
      apiFetch<Project>("/projects", jsonInit("POST", input)),
    get: (projectId: string) => apiFetch<Project>(`/projects/${projectId}`),
    update: (projectId: string, input: ProjectInput) =>
      apiFetch<Project>(`/projects/${projectId}`, jsonInit("PATCH", input)),
    remove: (projectId: string) =>
      apiFetch<void>(`/projects/${projectId}`, { method: "DELETE" }),
  },

  tasks: {
    list: (projectId: string, filters: TaskFilters = {}) => {
      const params = new URLSearchParams();
      if (filters.status) params.set("status", filters.status);
      if (filters.tag) params.set("tag", filters.tag);
      const query = params.size > 0 ? `?${params}` : "";
      return apiFetch<TaskSummary[]>(`/projects/${projectId}/tasks${query}`);
    },
    create: (projectId: string, input: TaskCreateInput) =>
      apiFetch<Task>(`/projects/${projectId}/tasks`, jsonInit("POST", input)),
    get: (taskId: string) => apiFetch<Task>(`/tasks/${taskId}`),
    update: (taskId: string, input: TaskUpdateInput) =>
      apiFetch<Task>(`/tasks/${taskId}`, jsonInit("PATCH", input)),
    remove: (taskId: string) =>
      apiFetch<void>(`/tasks/${taskId}`, { method: "DELETE" }),
  },

  attachments: {
    list: (taskId: string) =>
      apiFetch<Attachment[]>(`/tasks/${taskId}/attachments`),
    // multipart: sem Content-Type manual — o browser define o boundary
    upload: (taskId: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<Attachment>(`/tasks/${taskId}/attachments`, {
        method: "POST",
        body: form,
      });
    },
    remove: (attachmentId: string) =>
      apiFetch<void>(`/attachments/${attachmentId}`, { method: "DELETE" }),
    // URL absoluta de download — usada em <a href> e thumbnails <img>
    downloadUrl: (attachmentId: string) =>
      `${BASE_URL}/attachments/${attachmentId}/download`,
  },

  // Extensão além do escopo mínimo (ADR-003)
  assistant: {
    chat: (request: AssistantChatRequest) =>
      apiFetch<AssistantChatResponse>(
        "/assistant/chat",
        jsonInit("POST", request),
      ),
  },
};
