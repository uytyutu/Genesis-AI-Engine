"use client";

import type { OfficeProgressStep } from "../../lib/officeApi";
import { useOfficeT } from "../../lib/useOfficeT";

export function OfficeOrderProgress({
  steps,
  title,
}: {
  steps?: OfficeProgressStep[] | null;
  title?: string;
}) {
  const { t } = useOfficeT();
  const list = steps || [];
  if (!list.length) return null;

  return (
    <section className="vo-enter rounded-2xl border border-[var(--vo-border)] bg-[var(--vo-surface)] p-6 shadow-sm">
      <h2 className="vo-display text-2xl font-semibold">
        {title || t("progress.title")}
      </h2>
      <ol className="mt-5 space-y-3">
        {list.map((step) => {
          const mark =
            step.state === "done"
              ? "✓"
              : step.state === "active"
                ? "●"
                : step.state === "failed"
                  ? "✗"
                  : "○";
          const color =
            step.state === "done"
              ? "text-[var(--vo-ok)]"
              : step.state === "active"
                ? "text-[var(--vo-accent)]"
                : step.state === "failed"
                  ? "text-red-700"
                  : "text-[var(--vo-muted)]";
          return (
            <li key={step.id} className={`flex items-center gap-3 text-sm ${color}`}>
              <span
                className={`inline-flex h-7 w-7 items-center justify-center rounded-full border text-xs font-semibold ${
                  step.state === "active" ? "vo-pulse border-[var(--vo-accent)]" : "border-current"
                }`}
              >
                {mark}
              </span>
              <span className="font-medium">
                {t(`progress.${step.id}`) !== `progress.${step.id}`
                  ? t(`progress.${step.id}`)
                  : step.label_de}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
