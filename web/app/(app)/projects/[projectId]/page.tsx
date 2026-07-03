import { TasksView } from "./tasks-view";

// Título dinâmico ("<nome do projeto> — Taskly") é definido client-side na
// TasksView — o nome vem de request autenticado por cookie, fora do alcance
// de generateMetadata aqui.
export default async function ProjectTasksPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <TasksView projectId={projectId} />;
}
