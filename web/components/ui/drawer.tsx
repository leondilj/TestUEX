"use client";

import { useEffect, useRef, type ReactNode } from "react";

// Drawer lateral (~480px, direita — T26 §6) sobre <dialog> nativo:
// showModal() dá focus trap e restauração de foco ao card de origem.
// `hidden open:flex` no className: um display:flex incondicional derrota o
// `dialog:not([open]) { display: none }` nativo e o drawer fechado
// continuaria visível, engolindo os cliques da tela.
// Esc e clique no overlay NÃO fecham diretamente: pedem fechamento via
// onRequestClose — quem decide é o conteúdo (confirmação de descarte, T27 §3).
interface DrawerProps {
  open: boolean;
  onRequestClose: () => void;
  // id do heading que nomeia o dialog (aria-labelledby)
  labelledBy: string;
  children: ReactNode;
}

export function Drawer({
  open,
  onRequestClose,
  labelledBy,
  children,
}: DrawerProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={labelledBy}
      onCancel={(event) => {
        // Esc: intercepta o fechamento nativo e delega a decisão
        event.preventDefault();
        onRequestClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onRequestClose();
      }}
      className="fixed top-0 right-0 m-0 ml-auto hidden h-dvh max-h-dvh w-full max-w-[480px] flex-col bg-surface text-ink shadow-[0_8px_24px_rgba(28,27,26,0.08)] backdrop:bg-ink/40 open:flex"
    >
      {children}
    </dialog>
  );
}
