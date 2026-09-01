"use client";

import Link from "next/link";
import { ValueHunterPanel } from "../components/treasury/ValueHunterPanel";

export default function ValueHunterPage() {
  return (
    <main className="min-h-screen bg-zinc-950 px-4 py-8 text-zinc-100 md:px-8">
      <div className="mx-auto max-w-6xl space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b border-zinc-800 pb-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-wide text-emerald-600">Virtus Core · Research</p>
            <h1 className="text-2xl font-semibold text-emerald-300">Value Hunter</h1>
            <p className="mt-1 max-w-2xl text-sm text-zinc-400">
              Bounty discovery · expected value · legal report path. Не майнинг и не sweep чужих кошельков.
            </p>
          </div>
          <div className="flex gap-3 text-sm">
            <Link href="/treasury" className="text-zinc-400 hover:underline">
              ← Treasury
            </Link>
            <Link href="/compute" className="text-zinc-400 hover:underline">
              Compute
            </Link>
          </div>
        </div>
        <ValueHunterPanel />
      </div>
    </main>
  );
}
