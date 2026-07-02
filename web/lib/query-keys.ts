// Chaves centralizadas do TanStack Query — compartilhadas entre views e
// modais sem criar import circular. A chave de sessão vive em use-session.ts.

export const PROJECTS_QUERY_KEY = ["projects"] as const;
