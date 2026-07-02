import type { Metadata } from "next";

import { ProjectsView } from "./projects-view";

export const metadata: Metadata = {
  title: "Projetos — Taskly",
};

export default function ProjectsPage() {
  return <ProjectsView />;
}
