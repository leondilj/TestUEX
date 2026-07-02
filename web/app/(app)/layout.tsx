"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { api } from "@/lib/api-client";
import { consumeHadSession, useSession } from "@/lib/use-session";

// Layout (app): guarda de rota autenticada + topbar persistente (T26 §4).
// Sem sessão → /login; se havia sessão nesta aba, com aviso de expiração.
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user, isPending, isError } = useSession();

  useEffect(() => {
    if (isPending || user) return;
    router.replace(consumeHadSession() ? "/login?expired=1" : "/login");
  }, [isPending, user, router]);

  const logout = useMutation({
    mutationFn: api.auth.logout,
    onSettled: () => {
      // limpa todo o cache (projetos, tarefas) — nada vaza para o próximo login
      queryClient.clear();
      router.replace("/login");
    },
  });

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="animate-pulse" aria-hidden="true">
          <Logo size="lg" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
        <p className="text-ink-muted">
          Não foi possível conectar ao servidor. Verifique se a API está no ar.
        </p>
        <Button variant="secondary" onClick={() => router.refresh()}>
          Tentar de novo
        </Button>
      </div>
    );
  }

  // sem sessão: o useEffect acima já disparou o redirect
  if (!user) return null;

  return (
    <>
      <header className="border-b border-line bg-surface">
        <nav
          aria-label="Principal"
          className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4 sm:px-6"
        >
          <Link href="/projects" aria-label="Taskly — ir para projetos">
            <Logo />
          </Link>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-ink-muted sm:inline">
              {user.email}
            </span>
            <Button
              variant="secondary"
              onClick={() => logout.mutate()}
              loading={logout.isPending}
            >
              Sair
            </Button>
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        {children}
      </main>
    </>
  );
}
