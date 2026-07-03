"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Toast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api-client";
import { projectKeys, taskKeys } from "@/lib/query-keys";
import {
  TASK_STATUS_LABELS,
  type TaskFilters,
  type TaskStatus,
  type TaskSummary,
} from "@/lib/types";

import { TaskBoard } from "./task-board";
import { TaskDrawer, type TaskDrawerState } from "./task-drawer";
import { TaskFilterBar } from "./task-filter-bar";
import { TaskList } from "./task-list";
import { ViewToggle, type TaskView } from "./view-toggle";

const STATUS_UPDATE_ERROR =
  "Não foi possível atualizar o status. Tente novamente.";

// escolha de visualização persiste por projeto (T27 §2); default Lista.
// Só roda no browser: o guard de sessão do layout impede SSR desta árvore.
function storedView(projectId: string): TaskView {
  if (typeof window === "undefined") return "lista";
  const value = localStorage.getItem(`taskly:view:${projectId}`);
  return value === "kanban" ? "kanban" : "lista";
}

// Página do projeto (T31–T35): breadcrumb, toggle lista/kanban, filtros por
// status/tag (T35), mudança de status otimista no card (T32/ADR-004) e
// drawer de criar/editar (T33/T34).
export function TasksView({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [view, setView] = useState<TaskView>(() => storedView(projectId));
  // filtros sobrevivem à troca de visualização e ao drawer (T27 §2)
  const [filters, setFilters] = useState<TaskFilters>({});
  const [drawer, setDrawer] = useState<TaskDrawerState | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  // live region global (T26 §7) — feedback não-visual de mudanças assíncronas
  const [announcement, setAnnouncement] = useState("");

  const showToast = useCallback((message: string) => setToast(message), []);
  const dismissToast = useCallback(() => setToast(null), []);
  const announce = useCallback((message: string) => {
    // sufixo invisível alternado força o re-anúncio de mensagens repetidas
    setAnnouncement((prev) =>
      prev.replace(/ $/, "") === message ? `${message} ` : message,
    );
  }, []);

  const project = useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => api.projects.get(projectId),
    retry: (count, error) =>
      !(error instanceof ApiError && error.status === 404) && count < 2,
  });

  // T35: filtros viram query params — a filtragem é do backend (T20).
  // keepPreviousData evita o flash de skeleton a cada mudança de filtro.
  const tasks = useQuery({
    queryKey: projectKeys.tasks(projectId, filters),
    queryFn: () => api.tasks.list(projectId, filters),
    enabled: project.isSuccess,
    placeholderData: keepPreviousData,
  });

  // Coleção sem filtros alimenta as opções do select de tag (T27 §2). Sem
  // filtro ativo a chave coincide com a query acima — nenhum request extra.
  const allTasks = useQuery({
    queryKey: projectKeys.tasks(projectId),
    queryFn: () => api.tasks.list(projectId),
    enabled: project.isSuccess,
  });

  const tagOptions = useMemo(() => {
    const tags = new Set((allTasks.data ?? []).flatMap((task) => task.tags));
    // tag filtrada some das tarefas (editada/excluída)? mantém no select
    if (filters.tag) tags.add(filters.tag);
    return [...tags].sort((a, b) => a.localeCompare(b));
  }, [allTasks.data, filters.tag]);

  // título do documento por rota: "<nome do projeto> — Taskly" (T26 §7)
  useEffect(() => {
    if (project.data) document.title = `${project.data.name} — Taskly`;
  }, [project.data]);

  function changeView(next: TaskView) {
    setView(next);
    localStorage.setItem(`taskly:view:${projectId}`, next);
    announce(`Visualização em ${next}`);
  }

  // T32: update otimista — o card muda de coluna/badge na hora; falha
  // reverte + toast. Sem toast de sucesso (a movimentação É o feedback).
  const changeStatus = useMutation({
    mutationFn: ({ task, status }: { task: TaskSummary; status: TaskStatus }) =>
      api.tasks.update(task.id, { status }),
    onMutate: async ({ task, status }) => {
      // cancela pelo prefixo — pega a query filtrada e a de opções de tag
      await queryClient.cancelQueries({
        queryKey: projectKeys.tasks(projectId),
      });
      const activeKey = projectKeys.tasks(projectId, filters);
      const previous = queryClient.getQueryData<TaskSummary[]>(activeKey);
      queryClient.setQueryData<TaskSummary[]>(activeKey, (old) =>
        old?.map((t) => (t.id === task.id ? { ...t, status } : t)),
      );
      announce(`${task.title} movida para ${TASK_STATUS_LABELS[status]}`);
      return { previous, activeKey };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(context.activeKey, context.previous);
      }
      showToast(STATUS_UPDATE_ERROR);
    },
    onSuccess: (task) => {
      queryClient.setQueryData(taskKeys.detail(task.id), task);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.tasks(projectId) });
    },
  });

  const [drawerOpen, setDrawerOpen] = useState(false);

  function openDrawer(state: TaskDrawerState) {
    setDrawer(state);
    setDrawerOpen(true);
  }

  function closeDrawer() {
    setDrawerOpen(false);
    // cobre a tarefa excluída em outra aba (404 no drawer, T27 §3) e
    // qualquer edição salva — refetch barato da lista ao fechar
    queryClient.invalidateQueries({ queryKey: projectKeys.tasks(projectId) });
  }

  const notFound =
    project.error instanceof ApiError && project.error.status === 404;

  if (notFound) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <h1 className="font-display text-2xl font-semibold">
          Projeto não encontrado
        </h1>
        <p className="text-ink-muted">Ele pode ter sido excluído.</p>
        <Link
          href="/projects"
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
        >
          Voltar para projetos
        </Link>
      </div>
    );
  }

  if (project.isError || tasks.isError) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-ink-muted">
          Não foi possível carregar o projeto.
        </p>
        <Button
          variant="secondary"
          onClick={() => (project.isError ? project.refetch() : tasks.refetch())}
        >
          Tentar de novo
        </Button>
      </div>
    );
  }

  const loading = project.isPending || tasks.isPending;
  const empty = tasks.data?.length === 0;
  const filtersActive = Boolean(filters.status || filters.tag);

  return (
    <>
      <nav aria-label="Trilha" className="mb-1 text-sm text-ink-muted">
        <Link href="/projects" className="text-accent hover:underline">
          Projetos
        </Link>
        <span aria-hidden="true"> / </span>
        <span>{project.data?.name}</span>
      </nav>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="min-w-0 truncate font-display text-2xl font-semibold">
          {project.data?.name ?? "…"}
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          <ViewToggle value={view} onChange={changeView} />
          <TaskFilterBar
            filters={filters}
            tagOptions={tagOptions}
            onChange={setFilters}
          />
          <Button onClick={() => openDrawer({ kind: "create" })}>
            <span aria-hidden="true">+</span> Nova tarefa
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col gap-2" aria-hidden="true">
          {Array.from({ length: 4 }, (_, i) => (
            <div
              key={i}
              className="h-14 animate-pulse rounded-[10px] border border-line bg-surface"
            />
          ))}
        </div>
      ) : empty && filtersActive ? (
        <div className="flex flex-col items-center gap-3 rounded-[10px] border border-dashed border-line px-4 py-16 text-center">
          <h2 className="font-display text-lg font-semibold">
            Nenhuma tarefa encontrada
          </h2>
          <p className="text-sm text-ink-muted">
            Ajuste os filtros ou limpe-os.
          </p>
          <button
            type="button"
            onClick={() => setFilters({})}
            className="text-sm font-medium text-accent hover:underline"
          >
            Limpar filtros
          </button>
        </div>
      ) : empty && view === "lista" ? (
        <div className="flex flex-col items-center gap-3 rounded-[10px] border border-dashed border-line px-4 py-16 text-center">
          <h2 className="font-display text-lg font-semibold">
            Nenhuma tarefa ainda
          </h2>
          <p className="text-sm text-ink-muted">
            Crie a primeira tarefa deste projeto.
          </p>
          <Button className="mt-2" onClick={() => openDrawer({ kind: "create" })}>
            <span aria-hidden="true">+</span> Nova tarefa
          </Button>
        </div>
      ) : view === "lista" ? (
        <TaskList
          tasks={tasks.data ?? []}
          onOpenTask={(task) => openDrawer({ kind: "edit", taskId: task.id })}
          onChangeStatus={(task, status) => changeStatus.mutate({ task, status })}
        />
      ) : (
        <TaskBoard
          tasks={tasks.data ?? []}
          statusFilter={filters.status}
          onOpenTask={(task) => openDrawer({ kind: "edit", taskId: task.id })}
          onChangeStatus={(task, status) => changeStatus.mutate({ task, status })}
        />
      )}

      {/* drawer mantém o último state para a transição de fechamento */}
      {drawer && (
        <TaskDrawer
          open={drawerOpen}
          state={drawer}
          projectId={projectId}
          onClose={closeDrawer}
          onCreated={(task) => setDrawer({ kind: "edit", taskId: task.id })}
          onError={showToast}
          announce={announce}
        />
      )}

      <div aria-live="polite" className="sr-only">
        {announcement}
      </div>
      <Toast message={toast} onDismiss={dismissToast} />
    </>
  );
}
