"use client";

import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api-client";
import type { User } from "@/lib/types";

export const SESSION_QUERY_KEY = ["auth", "me"] as const;

// Marca que já houve sessão nesta aba — distingue "sessão expirou"
// (aviso no login, T26 §5) de um visitante que nunca logou
const HAD_SESSION_KEY = "taskly:had-session";

export function markHadSession() {
  try {
    sessionStorage.setItem(HAD_SESSION_KEY, "1");
  } catch {
    // sessionStorage indisponível (SSR/privacidade) — o aviso é opcional
  }
}

export function consumeHadSession(): boolean {
  try {
    const had = sessionStorage.getItem(HAD_SESSION_KEY) === "1";
    sessionStorage.removeItem(HAD_SESSION_KEY);
    return had;
  } catch {
    return false;
  }
}

// Sessão atual via GET /auth/me — `null` significa "sem sessão" (401),
// qualquer outra falha propaga como erro
export function useSession() {
  return useQuery<User | null>({
    queryKey: SESSION_QUERY_KEY,
    queryFn: async () => {
      try {
        const user = await api.auth.me();
        markHadSession();
        return user;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          return null;
        }
        throw error;
      }
    },
    staleTime: 60_000,
    retry: false,
  });
}
