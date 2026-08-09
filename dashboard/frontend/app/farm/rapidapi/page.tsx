"use client";

import Link from "next/link";
import { ApiFarmPanel } from "../../components/ApiFarmPanel";

export default function FarmRapidApiPage() {
  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-violet-300/80">Mission Control</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">API Farm · RapidAPI</h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            Discover → Build → Quality Gate → CEO Approve → Publish. Payout path: RapidAPI → PayPal.
            Stripe stays B2B. Potential revenue is never Actual.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Link href="/" className="text-sm text-emerald-300 hover:underline">
            ← Farm Dashboard
          </Link>
          <Link href="/business/api-markets" className="text-sm text-violet-300 hover:underline">
            Global Markets →
          </Link>
        </div>
      </div>
      <ApiFarmPanel />
    </main>
  );
}
