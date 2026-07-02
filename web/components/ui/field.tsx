"use client";

import type { InputHTMLAttributes, ReactNode } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  // erro inline abaixo do input, ligado via aria-describedby (T26 §7)
  error?: ReactNode;
  helperText?: string;
}

export function Field({
  id,
  label,
  error,
  helperText,
  className = "",
  ...props
}: FieldProps) {
  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;
  const describedBy =
    [error ? errorId : null, helperText ? helperId : null]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`rounded-lg border bg-surface px-3 py-2 text-sm placeholder:text-ink-muted ${
          error ? "border-danger" : "border-line"
        } ${className}`}
        {...props}
      />
      {helperText && (
        <p id={helperId} className="text-xs text-ink-muted">
          {helperText}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
