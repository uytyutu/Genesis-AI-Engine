"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ToastTone = "success" | "warning" | "info" | "payment";

export type ToastItem = {
  id: string;
  title: string;
  body?: string;
  tone: ToastTone;
  actionLabel?: string;
  onAction?: () => void;
};

type ToastContextValue = {
  push: (toast: Omit<ToastItem, "id">) => void;
  dismiss: (id: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const TONE_STYLES: Record<ToastTone, string> = {
  success: "border-emerald-500/40 bg-emerald-950/40",
  warning: "border-amber-500/40 bg-amber-950/40",
  info: "border-genesis-accent/40 bg-genesis-panel/90",
  payment: "border-violet-500/40 bg-violet-950/40",
};

const TONE_ICON: Record<ToastTone, string> = {
  success: "✅",
  warning: "⚠",
  info: "ℹ️",
  payment: "💰",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setItems((prev) => [...prev.slice(-4), { ...toast, id }]);
    window.setTimeout(() => dismiss(id), 8000);
  }, [dismiss]);

  const value = useMemo(() => ({ push, dismiss }), [push, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-3">
        {items.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto rounded-xl border p-4 shadow-2xl backdrop-blur ${TONE_STYLES[toast.tone]}`}
          >
            <p className="text-sm font-semibold text-white">
              {TONE_ICON[toast.tone]} {toast.title}
            </p>
            {toast.body && <p className="mt-1 text-xs text-genesis-muted">{toast.body}</p>}
            <div className="mt-3 flex gap-2">
              {toast.actionLabel && toast.onAction && (
                <button
                  type="button"
                  onClick={() => {
                    toast.onAction?.();
                    dismiss(toast.id);
                  }}
                  className="rounded-lg bg-genesis-accent px-3 py-1.5 text-xs font-medium text-white"
                >
                  {toast.actionLabel}
                </button>
              )}
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="rounded-lg border border-genesis-border px-3 py-1.5 text-xs text-genesis-muted"
              >
                Закрыть
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}
