"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type SubmitEvent,
} from "react";

import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/drawer";
import { Field } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { TagInput } from "@/components/ui/tag-input";
import { api, ApiError } from "@/lib/api-client";
import { isoToLocalInput, localInputToIso } from "@/lib/format";
import { projectKeys, taskKeys } from "@/lib/query-keys";
import {
  TASK_STATUS_LABELS,
  TASK_STATUSES,
  type Task,
  type TaskStatus,
  type TaskUpdateInput,
} from "@/lib/types";

import { AttachmentsSection } from "./attachments-section";

// Copy dos erros conforme T26/T27 — não parafrasear
const SAVE_ERROR = "Não foi possível salvar. Tente novamente.";
const DELETE_ERROR = "Não foi possível excluir. Tente novamente.";
const TITLE_REQUIRED = "Informe um título.";

const SHORT_DESCRIPTION_MAX = 280;
const COUNTER_VISIBLE_FROM = 200;
const COUNTER_LIVE_FROM = 260;

export type TaskDrawerState =
  | { kind: "create" }
  | { kind: "edit"; taskId: string };

interface TaskFormValues {
  title: string;
  shortDescription: string;
  fullDescription: string;
  // valor do <input type="datetime-local">; "" = sem prazo
  dueLocal: string;
  tags: string[];
  status: TaskStatus;
}

const EMPTY_FORM: TaskFormValues = {
  title: "",
  shortDescription: "",
  fullDescription: "",
  dueLocal: "",
  tags: [],
  status: "not_started",
};

function fromTask(task: Task): TaskFormValues {
  return {
    title: task.title,
    shortDescription: task.short_description ?? "",
    fullDescription: task.full_description ?? "",
    dueLocal: task.due_date ? isoToLocalInput(task.due_date) : "",
    tags: task.tags,
    status: task.status,
  };
}

function isDirty(values: TaskFormValues, baseline: TaskFormValues): boolean {
  return (
    values.title !== baseline.title ||
    values.shortDescription !== baseline.shortDescription ||
    values.fullDescription !== baseline.fullDescription ||
    values.dueLocal !== baseline.dueLocal ||
    values.status !== baseline.status ||
    values.tags.join("\n") !== baseline.tags.join("\n")
  );
}

// PATCH parcial (T27 §3): apenas os campos alterados; null limpa o campo —
// o backend usa exclude_unset, então campo omitido não é tocado
function buildPatch(
  values: TaskFormValues,
  baseline: TaskFormValues,
): TaskUpdateInput {
  const patch: TaskUpdateInput = {};
  if (values.title !== baseline.title) patch.title = values.title.trim();
  if (values.shortDescription !== baseline.shortDescription)
    patch.short_description = values.shortDescription.trim() || null;
  if (values.fullDescription !== baseline.fullDescription)
    patch.full_description = values.fullDescription.trim() || null;
  if (values.dueLocal !== baseline.dueLocal)
    patch.due_date = values.dueLocal ? localInputToIso(values.dueLocal) : null;
  if (values.status !== baseline.status) patch.status = values.status;
  if (values.tags.join("\n") !== baseline.tags.join("\n"))
    patch.tags = values.tags;
  return patch;
}

interface TaskDrawerProps {
  open: boolean;
  state: TaskDrawerState;
  projectId: string;
  onClose: () => void;
  // criação virou edição (T27 §3) — o pai troca o state para edit
  onCreated: (task: Task) => void;
  onError: (message: string) => void;
  announce: (message: string) => void;
}

// Drawer único de criar/editar tarefa (T27 §3). Criação vira edição após o
// 201 — o drawer não fecha (anexos exigem a tarefa criada, T34). Submit
// explícito; a exceção de imediatismo é o status no card (T32), fora daqui.
export function TaskDrawer({
  open,
  state,
  projectId,
  onClose,
  onCreated,
  onError,
  announce,
}: TaskDrawerProps) {
  const queryClient = useQueryClient();
  const titleHeadingId = useId();
  const fieldIds = useId();
  const titleInputRef = useRef<HTMLInputElement>(null);
  const keepEditingRef = useRef<HTMLButtonElement>(null);

  const [values, setValues] = useState<TaskFormValues>(EMPTY_FORM);
  const [baseline, setBaseline] = useState<TaskFormValues>(EMPTY_FORM);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [confirmingDiscard, setConfirmingDiscard] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  // id da tarefa cujos dados já popularam o formulário (evita reset em refetch)
  const [formLoadedId, setFormLoadedId] = useState<string | null>(null);

  const taskId = state.kind === "edit" ? state.taskId : null;

  const detail = useQuery({
    queryKey: taskKeys.detail(taskId ?? "pending"),
    queryFn: () => api.tasks.get(taskId!),
    enabled: open && taskId !== null,
    // 404 (tarefa excluída em outra aba) não deve ser retentado
    retry: (count, error) =>
      !(error instanceof ApiError && error.status === 404) && count < 2,
  });

  function resetForm(next: TaskFormValues) {
    setValues(next);
    setBaseline(next);
    setTitleError(null);
  }

  // a cada abertura, zera estados transientes; criação parte do form vazio —
  // ajuste de estado durante o render, sem effect
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setConfirmingDiscard(false);
      setConfirmingDelete(false);
      setFormLoadedId(null);
      if (state.kind === "create") resetForm(EMPTY_FORM);
    }
  }
  // edição: popula o form quando o detalhe chega (inclui a transição
  // criar→editar, cujo cache é semeado no onSuccess do create)
  if (open && detail.data && formLoadedId !== detail.data.id) {
    setFormLoadedId(detail.data.id);
    resetForm(fromTask(detail.data));
  }

  // autofocus no Título ao abrir em modo criação (T27 §3)
  useEffect(() => {
    if (open && state.kind === "create") titleInputRef.current?.focus();
  }, [open, state.kind]);

  // confirmação de descarte: foco na opção segura (T27 §5)
  useEffect(() => {
    if (confirmingDiscard) keepEditingRef.current?.focus();
  }, [confirmingDiscard]);

  const dirty = isDirty(values, baseline);

  const create = useMutation({
    mutationFn: () =>
      api.tasks.create(projectId, {
        title: values.title.trim(),
        short_description: values.shortDescription.trim() || null,
        full_description: values.fullDescription.trim() || null,
        due_date: values.dueLocal ? localInputToIso(values.dueLocal) : null,
        tags: values.tags,
      }),
    onSuccess: (task) => {
      queryClient.setQueryData(taskKeys.detail(task.id), task);
      queryClient.invalidateQueries({ queryKey: projectKeys.tasks(projectId) });
      announce("Tarefa criada");
      onCreated(task);
    },
    onError: () => onError(SAVE_ERROR),
  });

  const save = useMutation({
    mutationFn: (patch: TaskUpdateInput) => api.tasks.update(taskId!, patch),
    // salvar fecha o drawer (decisão do usuário em 2026-07-02, revisando a
    // UX spec §3 — o feedback é o card atualizado ao fundo + live region)
    onSuccess: (task) => {
      queryClient.setQueryData(taskKeys.detail(task.id), task);
      queryClient.invalidateQueries({ queryKey: projectKeys.tasks(projectId) });
      resetForm(fromTask(task));
      announce("Tarefa salva");
      onClose();
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 400) {
        setTitleError(TITLE_REQUIRED);
      } else {
        onError(SAVE_ERROR);
      }
    },
  });

  const remove = useMutation({
    mutationFn: () => api.tasks.remove(taskId!),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: taskKeys.detail(taskId!) });
      queryClient.invalidateQueries({ queryKey: projectKeys.tasks(projectId) });
      announce("Tarefa excluída");
      setConfirmingDelete(false);
      onClose();
    },
    onError: () => onError(DELETE_ERROR),
  });

  const shortTooLong = values.shortDescription.length > SHORT_DESCRIPTION_MAX;

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!values.title.trim()) {
      setTitleError(TITLE_REQUIRED);
      titleInputRef.current?.focus();
      return;
    }
    setTitleError(null);
    if (shortTooLong || create.isPending || save.isPending) return;
    if (state.kind === "create") {
      create.mutate();
    } else if (dirty) {
      save.mutate(buildPatch(values, baseline));
    }
  }

  function requestClose() {
    if (dirty) {
      setConfirmingDiscard(true);
    } else {
      onClose();
    }
  }

  const notFound =
    detail.error instanceof ApiError && detail.error.status === 404;
  const loading = state.kind === "edit" && detail.isPending;

  const drawerTitle =
    state.kind === "create"
      ? "Nova tarefa"
      : (detail.data?.title ?? "Tarefa");

  function set<K extends keyof TaskFormValues>(
    key: K,
    value: TaskFormValues[K],
  ) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <Drawer open={open} onRequestClose={requestClose} labelledBy={titleHeadingId}>
      <header className="flex items-center justify-between gap-4 border-b border-line px-6 py-4">
        <h2
          id={titleHeadingId}
          className="min-w-0 truncate font-display text-lg font-semibold"
        >
          {drawerTitle}
        </h2>
        <button
          type="button"
          aria-label="Fechar"
          onClick={requestClose}
          className="rounded-lg p-1.5 text-ink-muted transition-colors hover:bg-paper hover:text-ink"
        >
          ✕
        </button>
      </header>

      {notFound ? (
        // tarefa excluída em outra aba (T27 §3) — ao fechar, o pai refaz a lista
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
          <p className="text-ink-muted">Tarefa não encontrada</p>
          <Button variant="secondary" onClick={onClose}>
            Fechar
          </Button>
        </div>
      ) : detail.isError ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
          <p className="text-ink-muted">Não foi possível carregar a tarefa.</p>
          <Button variant="secondary" onClick={() => detail.refetch()}>
            Tentar de novo
          </Button>
        </div>
      ) : loading ? (
        <div className="flex flex-1 flex-col gap-4 px-6 py-6" aria-hidden="true">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="h-10 animate-pulse rounded-lg bg-paper" />
          ))}
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-6">
            <Field
              ref={titleInputRef}
              id={`${fieldIds}-title`}
              label="Título"
              required
              value={values.title}
              onChange={(e) => set("title", e.target.value)}
              error={titleError}
            />

            {state.kind === "edit" && (
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor={`${fieldIds}-status`}
                  className="text-sm font-medium"
                >
                  Status
                </label>
                <select
                  id={`${fieldIds}-status`}
                  value={values.status}
                  onChange={(e) => set("status", e.target.value as TaskStatus)}
                  className="rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                >
                  {TASK_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {TASK_STATUS_LABELS[status]}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <div className="flex items-baseline justify-between">
                <label
                  htmlFor={`${fieldIds}-short`}
                  className="text-sm font-medium"
                >
                  Descrição curta
                </label>
                {values.shortDescription.length >= COUNTER_VISIBLE_FROM && (
                  <span
                    aria-live={
                      values.shortDescription.length >= COUNTER_LIVE_FROM
                        ? "polite"
                        : "off"
                    }
                    className={`text-xs ${shortTooLong ? "font-medium text-danger" : "text-ink-muted"}`}
                  >
                    {values.shortDescription.length}/{SHORT_DESCRIPTION_MAX}
                  </span>
                )}
              </div>
              <input
                id={`${fieldIds}-short`}
                value={values.shortDescription}
                onChange={(e) => set("shortDescription", e.target.value)}
                aria-invalid={shortTooLong || undefined}
                className={`rounded-lg border bg-surface px-3 py-2 text-sm placeholder:text-ink-muted ${
                  shortTooLong ? "border-danger" : "border-line"
                }`}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label
                htmlFor={`${fieldIds}-full`}
                className="text-sm font-medium"
              >
                Descrição completa
              </label>
              <textarea
                id={`${fieldIds}-full`}
                rows={4}
                value={values.fullDescription}
                onChange={(e) => set("fullDescription", e.target.value)}
                className="max-h-72 min-h-24 resize-y rounded-lg border border-line bg-surface px-3 py-2 text-sm placeholder:text-ink-muted"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label
                htmlFor={`${fieldIds}-due`}
                className="text-sm font-medium"
              >
                Prazo
              </label>
              <div className="flex items-center gap-2">
                <input
                  id={`${fieldIds}-due`}
                  type="datetime-local"
                  value={values.dueLocal}
                  onChange={(e) => set("dueLocal", e.target.value)}
                  className="flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm"
                />
                {values.dueLocal && (
                  <Button
                    type="button"
                    variant="text"
                    onClick={() => set("dueLocal", "")}
                  >
                    Limpar
                  </Button>
                )}
              </div>
            </div>

            <TagInput
              id={`${fieldIds}-tags`}
              label="Tags"
              tags={values.tags}
              onChange={(tags) => set("tags", tags)}
            />

            {/* anexos só em modo edição — exigem a tarefa criada (T34) */}
            {state.kind === "edit" && detail.data && (
              <AttachmentsSection
                taskId={detail.data.id}
                attachments={detail.data.attachments}
                announce={announce}
                onError={onError}
              />
            )}
          </div>

          <footer className="border-t border-line px-6 py-4">
            {confirmingDiscard ? (
              // confirmação de descarte inline no rodapé (T27 §3) — sem window.confirm
              <div className="flex items-center justify-between gap-4">
                <span className="text-sm font-medium">
                  Descartar alterações?
                </span>
                <div className="flex gap-2">
                  <Button
                    ref={keepEditingRef}
                    type="button"
                    variant="secondary"
                    onClick={() => setConfirmingDiscard(false)}
                  >
                    Continuar editando
                  </Button>
                  <Button type="button" variant="danger" onClick={onClose}>
                    Descartar
                  </Button>
                </div>
              </div>
            ) : state.kind === "create" ? (
              <div className="flex justify-end gap-2">
                <Button type="button" variant="text" onClick={requestClose}>
                  Cancelar
                </Button>
                <Button type="submit" loading={create.isPending}>
                  Criar tarefa
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-4">
                <Button
                  type="button"
                  variant="danger-text"
                  onClick={() => setConfirmingDelete(true)}
                >
                  Excluir tarefa
                </Button>
                <Button type="submit" loading={save.isPending} disabled={!dirty}>
                  Salvar
                </Button>
              </div>
            )}
          </footer>
        </form>
      )}

      {/* confirmação de exclusão (dialog aninhado no top layer) */}
      <Modal
        open={confirmingDelete}
        onClose={() => setConfirmingDelete(false)}
        labelledBy={`${fieldIds}-delete-title`}
      >
        <div className="flex flex-col gap-4">
          <h2
            id={`${fieldIds}-delete-title`}
            className="font-display text-lg font-semibold"
          >
            Excluir tarefa?
          </h2>
          <p className="text-sm text-ink-muted">
            &ldquo;{detail.data?.title}&rdquo; e seus anexos serão excluídos
            permanentemente.
          </p>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirmingDelete(false)}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              variant="danger"
              loading={remove.isPending}
              onClick={() => remove.mutate()}
            >
              Excluir
            </Button>
          </div>
        </div>
      </Modal>
    </Drawer>
  );
}
