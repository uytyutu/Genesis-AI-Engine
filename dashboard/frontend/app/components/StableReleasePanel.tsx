"use client";

import { GenesisCard } from "./GenesisCard";

type StableReleaseDisplay = {
  brand?: string;
  stable_release?: {
    active?: {
      label?: string;
      title?: string;
      git_commit?: string;
      build_id?: string;
      activated_at?: string;
      approved_by?: string;
      product_blocks?: string[];
    } | null;
    label?: string | null;
    title?: string | null;
    git_commit?: string | null;
    build_id?: string | null;
    activated_display?: string;
    approved_by?: string | null;
    product_blocks?: string[];
  };
  release_status?: {
    status?: string;
    status_label?: string;
    rollback_available?: boolean;
  };
  history?: Array<{ label: string; title: string; git_commit?: string }>;
};

function formatActivated(iso?: string, fallback?: string) {
  if (fallback) return fallback;
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("de-DE");
  } catch {
    return iso.slice(0, 10);
  }
}

export function StableReleasePanel({ data }: { data?: StableReleaseDisplay | null }) {
  if (!data?.stable_release?.active && !data?.stable_release?.label) {
    return null;
  }

  const sr = data.stable_release;
  const active = sr?.active;
  const label = sr?.label ?? active?.label ?? "—";
  const title = sr?.title ?? active?.title;
  const commit = sr?.git_commit ?? active?.git_commit ?? active?.build_id?.slice(0, 12);
  const activated = formatActivated(active?.activated_at, sr?.activated_display);
  const statusLabel = data.release_status?.status_label ?? "Stable Release";

  return (
    <GenesisCard className="border-emerald-500/20 bg-emerald-950/10">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="genesis-label text-emerald-200/80">Virtus Core · Stable Release</p>
          <p className="mt-1 text-lg font-semibold text-white">{label}</p>
          {title ? <p className="text-sm text-genesis-muted">{title}</p> : null}
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-200">
          {statusLabel}
        </span>
      </div>
      <dl className="mt-4 grid gap-1 text-xs text-genesis-muted sm:grid-cols-2">
        {commit ? (
          <div>
            <dt className="inline font-medium text-genesis-text">Build </dt>
            <dd className="inline font-mono">{commit}</dd>
          </div>
        ) : null}
        {activated ? (
          <div>
            <dt className="inline font-medium text-genesis-text">Activated </dt>
            <dd className="inline">{activated}</dd>
          </div>
        ) : null}
        {active?.approved_by ? (
          <div className="sm:col-span-2">
            <dt className="inline font-medium text-genesis-text">Approved </dt>
            <dd className="inline">{active.approved_by}</dd>
          </div>
        ) : null}
      </dl>
      {data.history && data.history.length > 1 ? (
        <p className="mt-3 text-[11px] text-genesis-muted">
          История: {data.history.slice(0, 3).map((h) => `${h.label} ${h.title}`).join(" · ")}
        </p>
      ) : null}
    </GenesisCard>
  );
}
