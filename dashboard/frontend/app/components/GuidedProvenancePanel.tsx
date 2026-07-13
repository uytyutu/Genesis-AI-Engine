"use client";

import { buildPreviewProvenance, GUIDED_PRODUCT_PROMISE } from "../lib/guidedOwnership";
import type { GuidedCommerceState } from "../lib/guidedCommerce";
import { SpringIn } from "./motion/SpringIn";

type Props = {
  state: GuidedCommerceState;
  compact?: boolean;
};

export function GuidedTrustPromise({ className = "" }: { className?: string }) {
  return (
    <p
      className={`rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-3 py-2.5 text-xs leading-relaxed text-emerald-100 ${className}`}
    >
      {GUIDED_PRODUCT_PROMISE}
    </p>
  );
}

export function GuidedProvenancePanel({ state, compact }: Props) {
  const name = state.companyName.trim();
  if (!state.goalId || !name) return null;

  const lines = buildPreviewProvenance(state);

  return (
    <SpringIn className={compact ? "mt-3" : "mt-4"}>
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-genesis-accent">
        Как собран ваш сайт
      </p>
      <ul className="mt-2 space-y-1.5">
        {lines.map((line) => (
          <li
            key={line.id}
            className="rounded-lg border border-white/8 bg-white/[0.03] px-2.5 py-2 text-[11px] leading-snug"
          >
            <span className="font-medium text-white">{line.answer}</span>
            <span className="mx-1 text-genesis-muted">→</span>
            <span className="text-genesis-muted">{line.becomes}</span>
          </li>
        ))}
        <li className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-2 text-[11px] text-emerald-100">
          После оплаты → именно эта версия станет вашим сайтом
        </li>
      </ul>
    </SpringIn>
  );
}
