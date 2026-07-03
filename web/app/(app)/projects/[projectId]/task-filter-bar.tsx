"use client";

import {
  TASK_STATUS_LABELS,
  TASK_STATUSES,
  type TaskFilters,
  type TaskStatus,
} from "@/lib/types";

interface TaskFilterBarProps {
  filters: TaskFilters;
  // tags distintas das tarefas do projeto (sem filtro) — ver open question
  // T27 §6.2: tags de tarefas filtradas fora podem não aparecer
  tagOptions: string[];
  onChange: (filters: TaskFilters) => void;
}

// Filtros por status/tag (T35, T27 §2): combinam em E lógico e viram query
// params do GET /projects/{id}/tasks — a filtragem é do backend, refetch a
// cada mudança. Filtro ativo: borda accent + "×" para limpar individualmente.
export function TaskFilterBar({
  filters,
  tagOptions,
  onChange,
}: TaskFilterBarProps) {
  return (
    <div className="flex items-center gap-2">
      <FilterSelect
        prefix="Status"
        allLabel="Todos"
        ariaLabel="Filtrar por status"
        clearLabel="Limpar filtro de status"
        value={filters.status ?? ""}
        options={TASK_STATUSES.map((status) => ({
          value: status,
          label: TASK_STATUS_LABELS[status],
        }))}
        onChange={(value) =>
          onChange({ ...filters, status: (value || undefined) as TaskStatus })
        }
      />
      <FilterSelect
        prefix="Tag"
        allLabel="Todas"
        ariaLabel="Filtrar por tag"
        clearLabel="Limpar filtro de tag"
        value={filters.tag ?? ""}
        options={tagOptions.map((tag) => ({ value: tag, label: `#${tag}` }))}
        onChange={(value) => onChange({ ...filters, tag: value || undefined })}
      />
    </div>
  );
}

interface FilterSelectProps {
  prefix: string;
  allLabel: string;
  ariaLabel: string;
  clearLabel: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

function FilterSelect({
  prefix,
  allLabel,
  ariaLabel,
  clearLabel,
  value,
  options,
  onChange,
}: FilterSelectProps) {
  const active = value !== "";
  // sem opções e sem filtro ativo (ex.: projeto sem tags) — controle inerte
  const disabled = options.length === 0 && !active;

  return (
    <span
      className={`inline-flex items-center rounded-lg border bg-surface text-sm transition-colors ${
        active ? "border-accent" : "border-line"
      } ${disabled ? "opacity-50" : ""}`}
    >
      <span
        aria-hidden="true"
        className="pointer-events-none pl-2.5 text-ink-muted"
      >
        {prefix}:
      </span>
      <select
        aria-label={ariaLabel}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className={`cursor-pointer appearance-none bg-transparent py-1.5 pl-1 ${
          active ? "pr-1 font-medium" : "pr-7 text-ink-muted"
        }`}
      >
        <option value="">{allLabel}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {active ? (
        <button
          type="button"
          aria-label={clearLabel}
          onClick={() => onChange("")}
          className="px-2 py-1.5 text-ink-muted transition-colors hover:text-ink"
        >
          <span aria-hidden="true">×</span>
        </button>
      ) : (
        <svg
          width="12"
          height="12"
          viewBox="0 0 16 16"
          fill="none"
          aria-hidden="true"
          className="pointer-events-none -ml-5 mr-2 text-ink-muted"
        >
          <path
            d="M4 6l4 4 4-4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </span>
  );
}
