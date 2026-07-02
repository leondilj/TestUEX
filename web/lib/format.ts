// Datas sempre em pt-BR (ux-spec-navigation-and-identity.md §3).
// A API trafega ISO 8601 UTC; a conversão para exibição acontece aqui.

import type { TaskStatus } from "@/lib/types";

const DATE_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

// dd/mm HH:mm — metadados compactos dos cards de tarefa (T27 §2)
const SHORT_DATE_TIME_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatDate(iso: string): string {
  return DATE_FORMATTER.format(new Date(iso));
}

export function formatShortDateTime(iso: string): string {
  return SHORT_DATE_TIME_FORMATTER.format(new Date(iso));
}

// Prazo vencido só conta para tarefas ainda "vivas" (T27 §2)
export function isOverdue(dueDate: string, status: TaskStatus): boolean {
  if (status === "done" || status === "cancelled") return false;
  return new Date(dueDate).getTime() < Date.now();
}

// ---- Conversão ISO UTC ↔ <input type="datetime-local"> ----
// O input trabalha em horário local sem timezone ("2026-06-28T18:00");
// a API espera/devolve ISO UTC. A conversão usa o fuso do navegador.

export function isoToLocalInput(iso: string): string {
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

export function localInputToIso(local: string): string {
  return new Date(local).toISOString();
}
