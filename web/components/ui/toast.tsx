"use client";

import { useEffect } from "react";

const TOAST_DURATION_MS = 5000;

// Toast não bloqueante (T26 §5) — a live region fica sempre montada para o
// screen reader anunciar a mensagem quando ela aparecer.
// `onDismiss` precisa ser estável (useCallback) para não reiniciar o timer.
export function Toast({
  message,
  onDismiss,
}: {
  message: string | null;
  onDismiss: () => void;
}) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(onDismiss, TOAST_DURATION_MS);
    return () => clearTimeout(timer);
  }, [message, onDismiss]);

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-6 z-30 flex justify-center px-4"
    >
      {message && (
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg bg-ink px-4 py-2.5 text-sm text-white shadow-[0_8px_24px_rgba(28,27,26,0.24)]">
          {message}
          <button
            type="button"
            aria-label="Fechar aviso"
            onClick={onDismiss}
            className="text-white/70 transition-colors hover:text-white"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
