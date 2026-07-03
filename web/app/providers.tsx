"use client";

import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/lib/api-client";
import { SESSION_QUERY_KEY } from "@/lib/use-session";

export default function Providers({ children }: { children: React.ReactNode }) {
  // useState garante um QueryClient por montagem — nunca compartilhado entre requests no SSR
  const [queryClient] = useState(() => {
    // 401 em qualquer chamada da API = sessão expirou → zera a sessão no
    // cache e o guard do layout (app) redireciona para /login?expired=1
    // (T26 §4). Login/registro não passam por aqui (chamadas diretas no
    // form) — senha errada não derruba a sessão.
    const onUnauthorized = (error: unknown) => {
      if (error instanceof ApiError && error.status === 401) {
        client.setQueryData(SESSION_QUERY_KEY, null);
      }
    };
    const client: QueryClient = new QueryClient({
      queryCache: new QueryCache({ onError: onUnauthorized }),
      mutationCache: new MutationCache({ onError: onUnauthorized }),
    });
    return client;
  });

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
