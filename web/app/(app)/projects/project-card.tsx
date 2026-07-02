"use client";

import Link from "next/link";

import { Menu } from "@/components/ui/menu";
import { formatDate } from "@/lib/format";
import type { Project } from "@/lib/types";

interface ProjectCardProps {
  project: Project;
  onRename: () => void;
  onDelete: () => void;
}

// Card da grade de projetos (T26 §6): o card inteiro navega para o projeto
// via overlay do link; o menu ⋯ fica acima do overlay (z-10)
export function ProjectCard({ project, onRename, onDelete }: ProjectCardProps) {
  return (
    <li
      data-project-id={project.id}
      className="relative rounded-[10px] border border-line bg-surface p-5 transition-colors hover:border-accent"
    >
      <Link
        href={`/projects/${project.id}`}
        className="block truncate pr-8 font-display text-base font-semibold before:absolute before:inset-0 before:rounded-[10px]"
      >
        {project.name}
      </Link>
      <p className="mt-1 text-sm text-ink-muted">
        criado em {formatDate(project.created_at)}
      </p>
      <div className="absolute top-3 right-3 z-10">
        <Menu
          label={`Ações do projeto ${project.name}`}
          items={[
            { label: "Renomear", onSelect: onRename },
            { label: "Excluir", onSelect: onDelete, danger: true },
          ]}
        />
      </div>
    </li>
  );
}
