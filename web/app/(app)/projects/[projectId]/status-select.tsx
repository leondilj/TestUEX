"use client";

import {
  TASK_STATUS_LABELS,
  TASK_STATUSES,
  type TaskStatus,
} from "@/lib/types";

const STATUS_BADGE_CLASSES: Record<TaskStatus, string> = {
  not_started: "bg-status-not-started-bg text-status-not-started-fg",
  in_progress: "bg-status-in-progress-bg text-status-in-progress-fg",
  done: "bg-status-done-bg text-status-done-fg",
  cancelled: "bg-status-cancelled-bg text-status-cancelled-fg",
};

interface StatusSelectProps {
  taskTitle: string;
  value: TaskStatus;
  onChange: (status: TaskStatus) => void;
  // badge = pill colorida na linha da lista; control = rodapé do card kanban
  variant: "badge" | "control";
}

// Controle explícito de status no card (ADR-004 — sem drag-and-drop).
// <select> nativo: menu de 4 opções com a atual marcada, teclado e screen
// reader de graça. stopPropagation para o clique não abrir o drawer (T27 §2).
export function StatusSelect({
  taskTitle,
  value,
  onChange,
  variant,
}: StatusSelectProps) {
  const variantClasses =
    variant === "badge"
      ? `rounded-full py-0.5 pr-6 pl-2.5 text-xs font-medium ${STATUS_BADGE_CLASSES[value]}`
      : "w-full rounded-lg border border-line bg-surface py-1.5 pr-7 pl-2.5 text-xs text-ink-muted hover:border-accent";

  // cor do chevron acompanha o texto do select (fica no span por fora dele)
  const chevronColor =
    variant === "badge"
      ? STATUS_BADGE_CLASSES[value].split(" ")[1]
      : "text-ink-muted";

  return (
    <span className={`relative z-10 inline-flex ${variant === "control" ? "w-full" : ""} ${chevronColor}`}>
      <select
        aria-label={`Status de ${taskTitle}`}
        value={value}
        onChange={(event) => onChange(event.target.value as TaskStatus)}
        onClick={(event) => event.stopPropagation()}
        className={`cursor-pointer appearance-none ${variantClasses}`}
      >
        {TASK_STATUSES.map((status) => (
          <option key={status} value={status}>
            {TASK_STATUS_LABELS[status]}
          </option>
        ))}
      </select>
      <svg
        width="12"
        height="12"
        viewBox="0 0 16 16"
        fill="none"
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 right-2 -translate-y-1/2"
      >
        <path
          d="M4 6l4 4 4-4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
