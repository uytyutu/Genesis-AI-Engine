"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Timeline = {
  progress_percent: number;
  label: string;
  milestones: { id: string; label: string; status: string; symbol: string }[];
};

export function ProjectTimeline() {
  const [data, setData] = useState<Timeline | null>(null);

  useEffect(() => {
    fetch(`${API}/api/owner/timeline`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null));
  }, []);

  if (!data) return null;

  const filled = Math.round((data.progress_percent / 100) * 24);

  return (
    <section className="rounded-xl border border-genesis-border bg-genesis-panel p-6">
      <div className="mb-2 flex items-end justify-between">
        <h3 className="text-sm font-medium uppercase tracking-wider text-genesis-muted">
          {data.label}
        </h3>
        <span className="text-2xl font-semibold">{data.progress_percent}%</span>
      </div>
      <div className="mb-4 font-mono text-sm tracking-widest text-genesis-accent">
        {"█".repeat(filled)}
        <span className="text-genesis-border">{"░".repeat(24 - filled)}</span>
      </div>
      <ul className="grid gap-1 text-sm sm:grid-cols-2">
        {data.milestones.map((m) => (
          <li
            key={m.id}
            className={
              m.status === "done"
                ? "text-genesis-green"
                : m.status === "active"
                  ? "text-yellow-400"
                  : "text-genesis-muted"
            }
          >
            {m.symbol} {m.label}
          </li>
        ))}
      </ul>
    </section>
  );
}
