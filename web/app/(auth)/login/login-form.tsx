"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, type SubmitEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { api, ApiError } from "@/lib/api-client";
import { markHadSession, SESSION_QUERY_KEY } from "@/lib/use-session";

export function LoginForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Aviso discreto quando a guarda de rota redirecionou por sessão expirada
  // (T26 §4) — a page envolve este form em <Suspense> por causa deste hook
  const expired = useSearchParams().get("expired") === "1";

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await api.auth.login({ email, password });
      markHadSession();
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      router.replace("/projects");
    } catch (err) {
      // 401: copy exata da T26 — nunca dizer qual campo errou, manter e-mail
      setError(
        err instanceof ApiError && err.status === 401
          ? "E-mail ou senha incorretos."
          : "Não foi possível entrar. Tente novamente.",
      );
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <h1 className="font-display text-2xl font-semibold">Entrar</h1>

      {expired && (
        <p className="text-sm text-ink-muted" role="status">
          Sua sessão expirou, entre novamente.
        </p>
      )}

      <Field
        id="email"
        label="E-mail"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <Field
        id="password"
        label="Senha"
        type="password"
        autoComplete="current-password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      {error && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}

      <Button type="submit" loading={submitting}>
        Entrar
      </Button>

      <p className="text-center text-sm text-ink-muted">
        Não tem conta?{" "}
        <Link href="/register" className="font-medium text-accent hover:underline">
          Criar conta
        </Link>
      </p>
    </form>
  );
}
