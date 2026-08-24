/** Shared Business Control Center UI primitives (B3). */

import Link from "next/link";
import type { ReactNode } from "react";
import type { HonestProductStatus } from "./clientProductStatus";

export const BCC_GLASS =
  "rounded-2xl border border-white/10 bg-white/[0.03] shadow-[0_0_28px_-20px_rgba(124,58,237,0.22)]";

export const BCC_GLASS_ACTIVE =
  "rounded-2xl border border-violet-500/30 bg-gradient-to-b from-violet-950/35 to-[#0c0a12] shadow-[0_0_36px_-22px_rgba(124,58,237,0.35)]";

export type BccTone = "active" | "pending" | "inactive" | "soon" | "unknown";

export function toneFromHonest(key: HonestProductStatus): BccTone {
  if (key === "active") return "active";
  if (key === "pending") return "pending";
  if (key === "coming_soon") return "soon";
  if (key === "not_activated") return "inactive";
  return "unknown";
}

const TONE_PILL: Record<BccTone, string> = {
  active: "border-emerald-400/35 bg-emerald-500/15 text-emerald-100",
  pending: "border-amber-400/35 bg-amber-500/15 text-amber-100",
  inactive: "border-white/15 bg-white/[0.04] text-zinc-400",
  soon: "border-violet-400/25 bg-violet-500/10 text-violet-200/90",
  unknown: "border-white/10 bg-white/[0.03] text-zinc-500",
};

const TONE_DOT: Record<BccTone, string> = {
  active: "bg-emerald-400",
  pending: "bg-amber-400",
  inactive: "bg-zinc-500",
  soon: "bg-violet-400",
  unknown: "bg-zinc-600",
};

export function BccStatusPill({
  tone,
  label,
}: {
  tone: BccTone;
  label: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${TONE_PILL[tone]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${TONE_DOT[tone]}`} aria-hidden />
      {label}
    </span>
  );
}

export function BccSectionHeader({
  title,
  actionHref,
  actionLabel,
}: {
  title: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-zinc-500">
        {title}
      </h2>
      {actionHref && actionLabel ? (
        <Link
          href={actionHref}
          className="text-sm font-medium text-violet-300 hover:text-violet-100"
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}

export function BccPanel({
  children,
  className = "",
  active = false,
}: {
  children: ReactNode;
  className?: string;
  active?: boolean;
}) {
  return (
    <div className={`${active ? BCC_GLASS_ACTIVE : BCC_GLASS} ${className}`}>
      {children}
    </div>
  );
}

export function BccPrimaryButton({
  href,
  children,
  tone = "active",
}: {
  href: string;
  children: ReactNode;
  tone?: BccTone;
}) {
  const cls =
    tone === "active"
      ? "bg-violet-600 text-white shadow-[0_8px_24px_-16px_rgba(124,58,237,0.55)] hover:bg-violet-500"
      : tone === "pending"
        ? "border border-amber-400/40 bg-amber-500/15 text-amber-50 hover:bg-amber-500/25"
        : "border border-white/15 bg-white/[0.04] text-zinc-100 hover:border-violet-400/40 hover:bg-violet-500/10";
  return (
    <Link
      href={href}
      className={`inline-flex min-h-[44px] w-full items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition ${cls}`}
    >
      {children}
    </Link>
  );
}

export function BccQuickLink({
  href,
  label,
  highlight = false,
}: {
  href: string;
  label: string;
  highlight?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex min-h-[44px] items-center justify-between rounded-xl border px-3 py-2.5 text-sm transition ${
        highlight
          ? "border-violet-400/25 bg-violet-500/10 text-violet-50 hover:bg-violet-500/15"
          : "border-white/8 text-zinc-200 hover:border-violet-400/35"
      }`}
    >
      <span>{label}</span>
      <span className={highlight ? "text-violet-300" : "text-zinc-500"}>→</span>
    </Link>
  );
}

export type BccCrumb = { label: string; href?: string };

/** Where-am-I trail — IA, not decoration. */
export function BccLocationTrail({
  crumbs,
  className = "",
}: {
  crumbs: BccCrumb[];
  className?: string;
}) {
  if (!crumbs.length) return null;
  return (
    <nav
      aria-label="Standort"
      className={`flex flex-wrap items-center gap-x-1.5 gap-y-1 text-[11px] text-zinc-500 ${className}`}
    >
      {crumbs.map((c, i) => {
        const last = i === crumbs.length - 1;
        return (
          <span key={`${c.label}-${i}`} className="inline-flex items-center gap-1.5">
            {i > 0 ? <span className="text-zinc-700" aria-hidden>→</span> : null}
            {c.href && !last ? (
              <Link href={c.href} className="text-zinc-400 hover:text-violet-200">
                {c.label}
              </Link>
            ) : (
              <span className={last ? "font-medium text-zinc-300" : undefined}>
                {c.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
