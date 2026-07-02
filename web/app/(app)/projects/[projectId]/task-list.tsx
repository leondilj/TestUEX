"use client";

import { formatShortDateTime, isOverdue } from "@/lib/format";
import type { TaskStatus, TaskSummary } from "@/lib/types";

import { StatusSelect } from "./status-select";

const VISIBLE_TAGS = 3;

interface TaskListProps {
  tasks: TaskSummary[];
  onOpenTask: (task: TaskSummary) => void;
  onChangeStatus: (task: TaskSummary, status: TaskStatus) => void;
}

// Modo lista (T27 §2): uma linha-card por tarefa, ordenada por created_at ASC
// (ordenação vem do backend — ADR-004). A linha inteira abre o drawer via
// overlay do botão do título; o badge de status fica acima do overlay (z-10).
export function TaskList({ tasks, onOpenTask, onChangeStatus }: TaskListProps) {
  return (
    <ul className="flex flex-col gap-2">
      {tasks.map((task) => (
        <li
          key={task.id}
          className="relative flex min-h-11 flex-wrap items-center gap-x-3 gap-y-1 rounded-[10px] border border-line bg-surface px-4 py-3 transition-colors hover:border-accent"
        >
          <StatusSelect
            taskTitle={task.title}
            value={task.status}
            onChange={(status) => onChangeStatus(task, status)}
            variant="badge"
          />
          <button
            type="button"
            onClick={() => onOpenTask(task)}
            className="min-w-0 flex-1 truncate text-left text-sm font-semibold before:absolute before:inset-0 before:rounded-[10px]"
          >
            {task.title}
          </button>
          {task.short_description && (
            <span className="hidden min-w-0 max-w-64 truncate text-sm text-ink-muted lg:inline">
              {task.short_description}
            </span>
          )}
          <span className="flex items-center gap-2">
            {task.due_date && <DueDate task={task} />}
            {task.tags.slice(0, VISIBLE_TAGS).map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-paper px-2.5 py-0.5 text-xs text-ink-muted"
              >
                #{tag}
              </span>
            ))}
            {task.tags.length > VISIBLE_TAGS && (
              <span className="text-xs text-ink-muted">
                +{task.tags.length - VISIBLE_TAGS}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function DueDate({ task }: { task: TaskSummary }) {
  if (!task.due_date) return null;
  const overdue = isOverdue(task.due_date, task.status);
  return (
    <span
      className={`whitespace-nowrap text-xs ${overdue ? "font-medium text-danger" : "text-ink-muted"}`}
    >
      <span aria-hidden="true">⏰ </span>
      {overdue && "Venceu "}
      {formatShortDateTime(task.due_date)}
    </span>
  );
}
