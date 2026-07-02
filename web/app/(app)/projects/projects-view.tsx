"use client";

import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Toast } from "@/components/ui/toast";
import { api } from "@/lib/api-client";
import { PROJECTS_QUERY_KEY } from "@/lib/query-keys";
import type { Project } from "@/lib/types";

import { ProjectCard } from "./project-card";
import { DeleteProjectModal, ProjectFormModal } from "./project-modals";

type ModalState =
  | { kind: "create" }
  | { kind: "rename"; project: Project }
  | { kind: "delete"; project: Project }
  | null;

const GRID_CLASSES = "grid gap-4 sm:grid-cols-2 lg:grid-cols-3";

export function ProjectsView() {
  const [modal, setModal] = useState<ModalState>(null);
  const [toast, setToast] = useState<string | null>(null);
  // id do projeto recém-criado — o foco move para o card dele (T26 §5)
  const [focusId, setFocusId] = useState<string | null>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const {
    data: projects,
    isPending,
    isError,
    refetch,
  } = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: api.projects.list,
  });

  useEffect(() => {
    if (!focusId) return;
    const card = listRef.current?.querySelector<HTMLElement>(
      `[data-project-id="${focusId}"] a`,
    );
    if (card) {
      card.focus();
      setFocusId(null);
    }
  }, [focusId, projects]);

  const closeModal = useCallback(() => setModal(null), []);
  const showToast = useCallback((message: string) => setToast(message), []);
  const dismissToast = useCallback(() => setToast(null), []);

  const formOpen = modal?.kind === "create" || modal?.kind === "rename";

  return (
    <>
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="font-display text-2xl font-semibold">Projetos</h1>
        {/* CTA fica no header só quando já existe projeto — no vazio o CTA é o do empty state */}
        {projects && projects.length > 0 && (
          <Button onClick={() => setModal({ kind: "create" })}>
            <span aria-hidden="true">+</span> Novo projeto
          </Button>
        )}
      </div>

      {isPending && (
        <ul className={GRID_CLASSES} aria-hidden="true">
          {Array.from({ length: 3 }, (_, i) => (
            <li
              key={i}
              className="h-24 animate-pulse rounded-[10px] border border-line bg-surface"
            />
          ))}
        </ul>
      )}

      {isError && (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <p className="text-ink-muted">
            Não foi possível carregar seus projetos.
          </p>
          <Button variant="secondary" onClick={() => refetch()}>
            Tentar de novo
          </Button>
        </div>
      )}

      {projects && projects.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-[10px] border border-dashed border-line px-4 py-16 text-center">
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
            className="text-accent"
          >
            <path
              d="M4 13l5 5L20 6"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <h2 className="font-display text-lg font-semibold">
            Crie seu primeiro projeto
          </h2>
          <p className="text-sm text-ink-muted">
            Projetos agrupam suas tarefas — comece com um.
          </p>
          <Button className="mt-2" onClick={() => setModal({ kind: "create" })}>
            Novo projeto
          </Button>
        </div>
      )}

      {projects && projects.length > 0 && (
        <ul ref={listRef} className={GRID_CLASSES}>
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onRename={() => setModal({ kind: "rename", project })}
              onDelete={() => setModal({ kind: "delete", project })}
            />
          ))}
        </ul>
      )}

      <ProjectFormModal
        open={formOpen}
        project={modal?.kind === "rename" ? modal.project : null}
        onClose={closeModal}
        onSaved={(saved) => {
          if (modal?.kind === "create") setFocusId(saved.id);
          setModal(null);
        }}
        onError={showToast}
      />
      <DeleteProjectModal
        open={modal?.kind === "delete"}
        project={modal?.kind === "delete" ? modal.project : null}
        onClose={closeModal}
        onError={showToast}
      />

      <Toast message={toast} onDismiss={dismissToast} />
    </>
  );
}
