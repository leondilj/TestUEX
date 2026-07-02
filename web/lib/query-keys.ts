// Chaves centralizadas do TanStack Query — compartilhadas entre views e
// modais sem criar import circular. A chave de sessão vive em use-session.ts.

import type { TaskFilters } from "@/lib/types";

export const PROJECTS_QUERY_KEY = ["projects"] as const;

export const projectKeys = {
  detail: (projectId: string) => ["projects", projectId] as const,
  // sem filtros na chave-base: invalidar ["projects", id, "tasks"] pega
  // todas as combinações de filtro (T35)
  tasks: (projectId: string, filters?: TaskFilters) =>
    filters && (filters.status || filters.tag)
      ? (["projects", projectId, "tasks", filters] as const)
      : (["projects", projectId, "tasks"] as const),
};

export const taskKeys = {
  detail: (taskId: string) => ["tasks", taskId] as const,
};
