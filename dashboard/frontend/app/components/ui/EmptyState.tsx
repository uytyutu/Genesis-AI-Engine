import Link from "next/link";
import type { ReactNode } from "react";
import { ButtonLink } from "./Button";

export function EmptyState({
  icon = "○",
  title,
  description,
  actionLabel,
  href,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  href?: string;
}) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-genesis-border-subtle bg-genesis-panel/30 px-6 py-12 text-center">
      <span className="text-3xl text-genesis-muted/80" aria-hidden>
        {icon}
      </span>
      <h3 className="mt-4 text-lg font-semibold text-genesis-text">{title}</h3>
      {description && <p className="mt-2 max-w-sm text-sm text-genesis-muted">{description}</p>}
      {actionLabel && href && (
        <div className="mt-6">
          <ButtonLink href={href} variant="secondary" size="md">
            {actionLabel}
          </ButtonLink>
        </div>
      )}
    </div>
  );
}
