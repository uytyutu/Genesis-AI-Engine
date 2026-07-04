"use client";

import { useEffect, type ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Button } from "./Button";

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
};

export function Modal({ open, onClose, title, children, className }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={cn(
          "relative z-10 w-full max-w-md animate-fade-up rounded-2xl border border-genesis-border bg-genesis-panel p-6 shadow-card",
          className
        )}
      >
        <h2 id="modal-title" className="text-lg font-semibold text-genesis-text">
          {title}
        </h2>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}

export function Dialog({
  open,
  onClose,
  title,
  description,
  confirmLabel = "Подтвердить",
  cancelLabel = "Отмена",
  onConfirm,
  variant = "primary",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  variant?: "primary" | "danger";
}) {
  return (
    <Modal open={open} onClose={onClose} title={title}>
      {description && <p className="text-sm text-genesis-muted">{description}</p>}
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={onClose}>
          {cancelLabel}
        </Button>
        <Button
          variant={variant === "danger" ? "danger" : "primary"}
          size="sm"
          onClick={() => {
            onConfirm();
            onClose();
          }}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
