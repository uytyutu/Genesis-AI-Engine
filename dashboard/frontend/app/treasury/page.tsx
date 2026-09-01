"use client";

import Link from "next/link";
import { TreasuryDashboard } from "../components/treasury/TreasuryDashboard";

/**
 * CEO — Value Hunter + казначейство (быстрый старт без тяжёлого Web3).
 */
export default function TreasuryPage() {
  return (
    <main className="min-h-screen bg-zinc-950 px-4 py-8 text-zinc-100 md:px-8">
      <div className="mx-auto max-w-6xl space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-zinc-800 pb-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-wide text-zinc-500">Virtus Core · Value Hunter</p>
            <h1 className="text-2xl font-semibold tracking-tight text-cyan-400">
              Treasury · Value Hunter v2 · Infrastructure
            </h1>
            <p className="mt-1 max-w-2xl text-sm text-zinc-400">
              ZERO-CAPITAL sources first. VCORE/Route Finder = инфраструктура. Цель: maximum realized BTC при €0
              капитале — без обещаний и без подделки ledger.
            </p>
          </div>
          <Link href="/executive" className="text-sm text-zinc-400 hover:text-zinc-200 hover:underline">
            ← CEO Dashboard
          </Link>
        </div>
        <TreasuryDashboard />
      </div>
    </main>
  );
}
