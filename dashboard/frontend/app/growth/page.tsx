"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  Mission2ConversionPanel,
  Mission2KpiTable,
  Mission2NextActionCard,
  type Mission2KpiData,
} from "../components/Mission2Kpi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function GrowthPage() {
  const [data, setData] = useState<Mission2KpiData | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/mission2-kpi`);
      if (res.ok) setData(await res.json());
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-2xl space-y-6">
        <header className="rounded-2xl border border-genesis-border bg-genesis-panel p-6">
          <Link href="/business" className="text-xs text-emerald-400 hover:underline">
            ← Business Health
          </Link>
          <p className="mt-2 text-xs uppercase tracking-[0.35em] text-genesis-muted">Mission 2</p>
          <h1 className="mt-2 text-2xl font-semibold">Конверсия</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Где именно тормозит путь к первому € — не красивая демонстрация, а диагностика.
          </p>
        </header>

        {data?.next_action ? <Mission2NextActionCard action={data.next_action} compact /> : null}

        {data ? (
          <Mission2ConversionPanel conversions={data.conversions} bottleneck={data.bottleneck_ru} />
        ) : null}

        {data?.metrics ? (
          <Mission2KpiTable metrics={data.metrics.filter((m) => m.id === "received" || m.format === "count")} title="Сводка" />
        ) : null}

        <div className="flex flex-wrap gap-2 text-sm">
          <Link href="/business/kpi" className="rounded-lg border border-white/10 px-3 py-1.5 hover:bg-white/5">
            Полная воронка →
          </Link>
          <Link href="/finance" className="rounded-lg border border-white/10 px-3 py-1.5 hover:bg-white/5">
            Получено · Stripe →
          </Link>
        </div>
      </div>
    </main>
  );
}
