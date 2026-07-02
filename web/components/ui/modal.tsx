"use client";

import { useEffect, useRef, type ReactNode } from "react";

// Modal sobre <dialog> nativo: showModal() dá focus trap, Esc e restauração
// de foco ao fechar de graça — sem lib externa (T26 §7)
interface ModalProps {
  open: boolean;
  onClose: () => void;
  // id do heading que nomeia o dialog (aria-labelledby)
  labelledBy: string;
  children: ReactNode;
}

export function Modal({ open, onClose, labelledBy, children }: ModalProps) {
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
      onClose={onClose}
      onClick={(event) => {
        // clique no backdrop (o próprio <dialog>) fecha; o conteúdo interno não
        if (event.target === event.currentTarget) onClose();
      }}
      className="m-auto w-full max-w-sm rounded-[10px] bg-surface p-6 text-ink shadow-[0_8px_24px_rgba(28,27,26,0.08)] backdrop:bg-ink/40"
    >
      {children}
    </dialog>
  );
}
