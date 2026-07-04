import type { InputHTMLAttributes, TextareaHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

const FIELD =
  "w-full rounded-xl border border-genesis-border bg-genesis-bg/80 px-3.5 py-2.5 text-sm text-genesis-text placeholder:text-genesis-muted/60 transition-colors duration-200 focus:border-genesis-accent focus:outline-none focus:ring-2 focus:ring-genesis-accent/25";

type FieldProps = {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
};

export function Field({ label, required, error, hint, children }: FieldProps) {
  return (
    <label className="block">
      <span className="genesis-label">
        {label}
        {required && <span className="text-rose-400" aria-hidden> *</span>}
      </span>
      <div className="mt-1.5">{children}</div>
      {error && (
        <p className="mt-1.5 text-xs text-rose-300" role="alert">
          {error}
        </p>
      )}
      {hint && !error && <p className="mt-1 text-xs text-genesis-muted">{hint}</p>}
    </label>
  );
}

export function Input({
  className,
  error,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { error?: boolean }) {
  return (
    <input
      className={cn(FIELD, error && "border-rose-500/50 focus:border-rose-400 focus:ring-rose-400/25", className)}
      {...props}
    />
  );
}

export function Textarea({
  className,
  error,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { error?: boolean }) {
  return (
    <textarea
      className={cn(
        FIELD,
        "min-h-[88px] resize-y",
        error && "border-rose-500/50 focus:border-rose-400 focus:ring-rose-400/25",
        className
      )}
      {...props}
    />
  );
}
