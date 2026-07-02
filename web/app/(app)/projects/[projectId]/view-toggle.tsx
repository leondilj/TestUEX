"use client";

export type TaskView = "lista" | "kanban";

const VIEW_LABELS: Record<TaskView, string> = {
  lista: "Lista",
  kanban: "Kanban",
};

interface ViewToggleProps {
  value: TaskView;
  onChange: (view: TaskView) => void;
}

// Segmented control Lista/Kanban (T27 §2 e §5): semanticamente é escolha
// exclusiva — radiogroup com dois radios, setas ←/→ alternam.
export function ViewToggle({ value, onChange }: ViewToggleProps) {
  const views: TaskView[] = ["lista", "kanban"];

  return (
    <div
      role="radiogroup"
      aria-label="Visualização"
      onKeyDown={(event) => {
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          const next = value === "lista" ? "kanban" : "lista";
          onChange(next);
          // roving tabindex: move o foco junto com a seleção
          const radio =
            event.currentTarget.querySelector<HTMLElement>(
              `[data-view="${next}"]`,
            );
          radio?.focus();
        }
      }}
      className="inline-flex rounded-lg border border-line bg-surface p-0.5"
    >
      {views.map((view) => {
        const active = view === value;
        return (
          <button
            key={view}
            type="button"
            role="radio"
            aria-checked={active}
            data-view={view}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(view)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              active
                ? "bg-accent text-white"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            {VIEW_LABELS[view]}
          </button>
        );
      })}
    </div>
  );
}
