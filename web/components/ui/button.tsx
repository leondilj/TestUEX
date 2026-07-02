"use client";

import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "text" | "danger" | "danger-text";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent-hover disabled:hover:bg-accent",
  secondary: "border border-line bg-surface text-ink hover:bg-paper",
  text: "text-accent hover:underline",
  // fundo vermelho sólido só na confirmação final (identidade, T26 §3)
  danger: "bg-danger text-white hover:bg-danger-hover disabled:hover:bg-danger",
  "danger-text": "text-danger hover:underline",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    >
      {loading && (
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          className="animate-spin"
        >
          <circle
            cx="12"
            cy="12"
            r="9"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray="42"
            strokeDashoffset="16"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
