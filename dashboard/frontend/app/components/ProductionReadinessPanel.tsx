"use client";

import Link from "next/link";

export type ReadinessLane = {
  id: string;
  label: string;
  status: "pass" | "in_progress" | "blocked" | "pending";
  note: string;
};

const STATUS_DOT: Record<ReadinessLane["status"], string> = {
  pass: "bg-emerald-400",
  in_progress: "bg-amber-400",
  blocked: "bg-rose-400",
  pending: "bg-zinc-500",
};

const STATUS_LABEL: Record<ReadinessLane["status"], string> = {
  pass: "Ready",
  in_progress: "In progress",
  blocked: "Blocked",
  pending: "Pending",
};

/** Honest Production Readiness — Overall never 100% while any lane is not green. */
export const DEFAULT_PRODUCTION_READINESS: ReadinessLane[] = [
  {
    id: "product",
    label: "Product",
    status: "pass",
    note: "G2.1 public storefront · Landing first · Meet Vector",
  },
  {
    id: "workspace",
    label: "Workspace",
    status: "pass",
    note: "G2.2 Client Workspace FINAL PASS",
  },
  {
    id: "security",
    label: "Security",
    status: "pass",
    note: "Security Gate S1 FINAL PASS · Freeze lifted",
  },
  {
    id: "infrastructure",
    label: "Infrastructure",
    status: "pass",
    note: "S1.2 PASS — headers · CSP · CORS · portal RL · HSTS · Secure cookie",
  },
  {
    id: "payments",
    label: "Payments",
    status: "pass",
    note: "G2.3 — Landing Path A sellable · other SKUs Coming Soon",
  },
  {
    id: "monitoring",
    label: "Monitoring",
    status: "pass",
    note: "Security Regression Suite 4/4 · OR metrics",
  },
];

export function readinessOverallPercent(lanes: ReadinessLane[]): number {
  const weight: Record<ReadinessLane["status"], number> = {
    pass: 100,
    in_progress: 45,
    pending: 15,
    blocked: 0,
  };
  if (lanes.length === 0) return 0;
  const allPass = lanes.every((lane) => lane.status === "pass");
  if (!allPass) {
    // Rule: Overall never reaches 100% while any mandatory lane is not green.
    const sum = lanes.reduce((acc, lane) => acc + weight[lane.status], 0);
    return Math.min(99, Math.round(sum / lanes.length));
  }
  return 100;
}

export function ProductionReadinessPanel({
  lanes = DEFAULT_PRODUCTION_READINESS,
}: {
  lanes?: ReadinessLane[];
}) {
  const overall = readinessOverallPercent(lanes);
  const securityOpen = lanes.some(
    (l) => l.id === "security" && l.status !== "pass",
  );

  return (
    <section className="rounded-2xl border border-white/10 bg-genesis-panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-400/80">
            Production Readiness
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">
            Virtus Core · release state
          </h2>
        </div>
        <div className="rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-right">
          <p className="text-xs text-zinc-500">Overall</p>
          <p className="text-2xl font-semibold text-white">{overall}%</p>
          {overall < 100 ? (
            <p className="mt-0.5 text-[10px] text-amber-200/80">
              Commercial Production Pending
            </p>
          ) : (
            <p className="mt-0.5 text-[10px] text-emerald-300">Production Ready</p>
          )}
        </div>
      </div>

      <ul className="mt-5 space-y-2">
        {lanes.map((lane) => (
          <li
            key={lane.id}
            className="flex flex-wrap items-start justify-between gap-2 rounded-xl border border-white/5 bg-black/20 px-3 py-2.5"
          >
            <div className="flex min-w-0 items-start gap-2">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[lane.status]}`}
                aria-hidden
              />
              <div>
                <p className="text-sm font-medium text-white">{lane.label}</p>
                <p className="text-xs text-zinc-500">{lane.note}</p>
              </div>
            </div>
            <span className="text-xs text-zinc-400">
              {STATUS_LABEL[lane.status]}
            </span>
          </li>
        ))}
      </ul>

      {securityOpen ? (
        <p className="mt-4 text-xs text-amber-100/90">
          Freeze active until Security Gate S1 PASS. No Marketplace · no new AI ·
          no new subscriptions.{" "}
          <Link href="/check" className="underline hover:text-white">
            Developer checks
          </Link>
        </p>
      ) : (
        <p className="mt-4 text-xs text-emerald-200/90">
          {overall >= 100
            ? "Production Ready. Next: G3.1 AI Support & Continuous Improvement (CEO)."
            : "Security Gate S1 complete · G2.3 until Overall 100%."}
        </p>
      )}
    </section>
  );
}
