"use client";

import Link from "next/link";

export type MissionDecision = {
  id: string;
  label: string;
  href: string;
};

export function OwnerDecisionsPanel({ decisions }: { decisions: MissionDecision[] }) {
  if (!decisions.length) return null;

  return (
    <section className="genesis-card animate-fade-up border-amber-500/20 bg-gradient-to-br from-amber-950/20 to-genesis-panel p-5">
      <p className="genesis-label text-amber-300/90">Требуется ваше решение</p>
      <ul className="mt-3 space-y-2">
        {decisions.map((d) => (
          <li key={d.id}>
            <Link
              href={d.href}
              className="flex items-center justify-between gap-3 rounded-xl border border-amber-500/25 bg-genesis-bg/40 px-4 py-3 text-sm transition hover:border-amber-400/40 hover:bg-amber-950/20"
            >
              <span>{d.label}</span>
              <span className="text-amber-300">→</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
