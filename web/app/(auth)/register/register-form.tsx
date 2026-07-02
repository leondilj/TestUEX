"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode, type SubmitEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { api, ApiError } from "@/lib/api-client";
import { markHadSession, SESSION_QUERY_KEY } from "@/lib/use-session";

const MIN_PASSWORD_LENGTH = 8;

export function RegisterForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState<ReactNode>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setEmailError(null);
    setPasswordError(null);
    setFormError(null);

    // validação client-side antes do request (T26 §5)
    if (password.length < MIN_PASSWORD_LENGTH) {
      setPasswordError("A senha precisa ter pelo menos 8 caracteres.");
      return;
    }

    setSubmitting(true);
    try {
      await api.auth.register({ email, password });
      // sucesso → login automático com as mesmas credenciais (T26 §5)
      const user = await api.auth.login({ email, password });
      markHadSession();
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
      router.replace("/projects");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setEmailError(
          <>
            Este e-mail já está cadastrado.{" "}
            <Link href="/login" className="font-medium text-accent hover:underline">
              Entrar
            </Link>
          </>,
        );
      } else if (err instanceof ApiError && err.status === 400) {
        setFormError(
          typeof err.detail === "string"
            ? err.detail
            : "Verifique os dados informados.",
        );
      } else {
        setFormError("Não foi possível criar a conta. Tente novamente.");
      }
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <h1 className="font-display text-2xl font-semibold">Criar conta</h1>

      <Field
        id="email"
        label="E-mail"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={emailError}
      />
      <Field
        id="password"
        label="Senha"
        type="password"
        autoComplete="new-password"
        required
        helperText="Mínimo de 8 caracteres"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={passwordError}
      />

      {formError && (
        <p role="alert" className="text-sm text-danger">
          {formError}
        </p>
      )}

      <Button type="submit" loading={submitting}>
        Criar conta
      </Button>

      <p className="text-center text-sm text-ink-muted">
        Já tem conta?{" "}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Entrar
        </Link>
      </p>
    </form>
  );
}
