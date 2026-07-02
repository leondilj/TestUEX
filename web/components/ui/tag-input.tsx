"use client";

import { useId, useState, type KeyboardEvent } from "react";

interface TagInputProps {
  id: string;
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
}

// Chip input de tags (T27 §3): Enter/vírgula adiciona, ✕ ou Backspace com
// campo vazio remove. Converte para minúsculas ao adicionar — espelha a
// normalização do backend, o usuário vê exatamente o que será salvo.
// Duplicadas são ignoradas silenciosamente.
export function TagInput({ id, label, tags, onChange }: TagInputProps) {
  const [draft, setDraft] = useState("");
  const hintId = useId();

  function commitDraft() {
    const tag = draft.trim().toLowerCase();
    setDraft("");
    if (tag && !tags.includes(tag)) onChange([...tags, tag]);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      commitDraft();
    } else if (event.key === "Backspace" && draft === "" && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <div
        role="group"
        aria-label={label}
        className="flex flex-wrap items-center gap-1.5 rounded-lg border border-line bg-surface px-2 py-1.5"
      >
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-paper px-2.5 py-0.5 text-xs text-ink"
          >
            #{tag}
            <button
              type="button"
              aria-label={`Remover tag ${tag}`}
              onClick={() => onChange(tags.filter((t) => t !== tag))}
              className="text-ink-muted transition-colors hover:text-danger"
            >
              ✕
            </button>
          </span>
        ))}
        <input
          id={id}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={commitDraft}
          aria-describedby={hintId}
          className="min-w-24 flex-1 bg-transparent px-1 py-0.5 text-sm outline-none placeholder:text-ink-muted"
          placeholder={tags.length === 0 ? "ex.: design, urgente" : undefined}
        />
        <span id={hintId} className="sr-only">
          Pressione Enter para adicionar
        </span>
      </div>
    </div>
  );
}
