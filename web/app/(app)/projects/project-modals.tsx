"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useId, useState, type SubmitEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { api } from "@/lib/api-client";
import { PROJECTS_QUERY_KEY } from "@/lib/query-keys";
import type { Project } from "@/lib/types";

// Copy dos erros conforme T26 §5 — não parafrasear
const SAVE_ERROR = "Não foi possível salvar. Tente novamente.";
const DELETE_ERROR = "Não foi possível excluir. Tente novamente.";

interface ProjectFormModalProps {
  open: boolean;
  // null = criar; com projeto = renomear
  project: Project | null;
  onClose: () => void;
  onSaved: (project: Project) => void;
  onError: (message: string) => void;
}

// Modal único de criar/renomear (campo único Nome — T26 §5). Em falha de
// rede o modal permanece aberto com o nome digitado + toast no pai.
export function ProjectFormModal({
  open,
  project,
  onClose,
  onSaved,
  onError,
}: ProjectFormModalProps) {
  const queryClient = useQueryClient();
  const titleId = useId();
  const [name, setName] = useState("");

  // a cada abertura, parte do nome atual (renomear) ou vazio (criar) —
  // ajuste de estado durante o render, sem effect
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) setName(project?.name ?? "");
  }

  const save = useMutation({
    mutationFn: (input: { name: string }) =>
      project
        ? api.projects.update(project.id, input)
        : api.projects.create(input),
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
      onSaved(saved);
    },
    onError: () => onError(SAVE_ERROR),
  });

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || save.isPending) return;
    save.mutate({ name: trimmed });
  }

  return (
    <Modal open={open} onClose={onClose} labelledBy={titleId}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <h2 id={titleId} className="font-display text-lg font-semibold">
          {project ? "Renomear projeto" : "Novo projeto"}
        </h2>
        <Field
          id="project-name"
          label="Nome"
          required
          maxLength={255}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="submit"
            loading={save.isPending}
            disabled={!name.trim()}
          >
            {project ? "Salvar" : "Criar"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

interface DeleteProjectModalProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onError: (message: string) => void;
}

// Confirmação de exclusão (T26 §5): "Cancelar" é o padrão (primeiro focável
// do dialog); "Excluir" é a única ação com fundo danger sólido do app
export function DeleteProjectModal({
  open,
  project,
  onClose,
  onError,
}: DeleteProjectModalProps) {
  const queryClient = useQueryClient();
  const titleId = useId();

  // mantém o último projeto para o conteúdo não sumir no frame de fechamento
  const [lastProject, setLastProject] = useState<Project | null>(null);
  if (project && project !== lastProject) setLastProject(project);
  const target = project ?? lastProject;

  const remove = useMutation({
    mutationFn: (projectId: string) => api.projects.remove(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY });
      onClose();
    },
    onError: () => onError(DELETE_ERROR),
  });

  if (!target) return null;

  return (
    <Modal open={open} onClose={onClose} labelledBy={titleId}>
      <div className="flex flex-col gap-4">
        <h2 id={titleId} className="font-display text-lg font-semibold">
          Excluir projeto?
        </h2>
        <p className="text-sm text-ink-muted">
          As tarefas e anexos de &ldquo;{target.name}&rdquo; serão excluídos
          permanentemente.
        </p>
        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="danger"
            loading={remove.isPending}
            onClick={() => remove.mutate(target.id)}
          >
            Excluir
          </Button>
        </div>
      </div>
    </Modal>
  );
}
