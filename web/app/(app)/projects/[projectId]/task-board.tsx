"use client";

import { useId } from "react";

import {
  TASK_STATUS_LABELS,
  TASK_STATUSES,
  type TaskStatus,
  type TaskSummary,
} from "@/lib/types";

import { StatusSelect } from "./status-select";
import { DueDate } from "./task-list";

const VISIBLE_TAGS = 2;

// Texto do cabeçalho na cor do status (tom -700 — T27 §2)
const COLUMN_HEADING_CLASSES: Record<TaskStatus, string> = {
  not_started: "text-status-not-started-fg",
  in_progress: "text-status-in-progress-fg",
  done: "text-status-done-fg",
  cancelled: "text-status-cancelled-fg",
};

interface TaskBoardProps {
  tasks: TaskSummary[];
  // filtro de status ativo (T35): só a coluna dele fica visível — as
  // demais colapsam; o filtro visível na barra explica o sumiço (T27 §2)
  statusFilter?: TaskStatus;
  onOpenTask: (task: TaskSummary) => void;
  onChangeStatus: (task: TaskSummary, status: TaskStatus) => void;
}

// Modo kanban (T27 §2): 4 colunas fixas, sempre visíveis mesmo vazias.
// Sem drag-and-drop (ADR-004) — mudança de status pelo select do card.
// <1024px: scroll horizontal com snap, colunas ~280px.
export function TaskBoard({
  tasks,
  statusFilter,
  onOpenTask,
  onChangeStatus,
}: TaskBoardProps) {
  const headingPrefix = useId();
  const columns = statusFilter ? [statusFilter] : TASK_STATUSES;

  return (
    <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 lg:grid lg:grid-cols-4 lg:overflow-visible">
      {columns.map((status) => {
        const columnTasks = tasks.filter((task) => task.status === status);
        const headingId = `${headingPrefix}-${status}`;
        return (
          <section
            key={status}
            aria-labelledby={headingId}
            className="w-70 shrink-0 snap-start lg:w-auto"
          >
            <h2
              id={headingId}
              className={`mb-3 text-sm font-semibold ${COLUMN_HEADING_CLASSES[status]}`}
            >
              {TASK_STATUS_LABELS[status]} ({columnTasks.length})
            </h2>
            {columnTasks.length === 0 ? (
              <p className="text-sm text-ink-muted">Sem tarefas</p>
            ) : (
              <ul className="flex flex-col gap-3">
                {columnTasks.map((task) => (
                  <li
                    key={task.id}
                    className="relative rounded-[10px] border border-line bg-surface p-3 transition-colors hover:border-accent"
                  >
                    <button
                      type="button"
                      onClick={() => onOpenTask(task)}
                      className="line-clamp-2 w-full text-left text-sm font-semibold before:absolute before:inset-0 before:rounded-[10px]"
                    >
                      {task.title}
                    </button>
                    {(task.due_date || task.tags.length > 0) && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <DueDate task={task} />
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
                      </div>
                    )}
                    <div className="mt-3">
                      <StatusSelect
                        taskTitle={task.title}
                        value={task.status}
                        onChange={(next) => onChangeStatus(task, next)}
                        variant="control"
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </div>
  );
}
