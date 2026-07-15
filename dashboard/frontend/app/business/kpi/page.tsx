"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  Mission2KpiTable,
  Mission2NextActionCard,
  type Mission2KpiData,
} from "../../components/Mission2Kpi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Mission2KpiPage() {
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
    void refresh();
    const t = setInterval(refresh, 20000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-2xl space-y-6">
        <header className="rounded-2xl border border-white/10 bg-genesis-panel p-6">
          <Link href="/business" className="text-xs text-emerald-400 hover:underline">
            ← Business Health
          </Link>
          <h1 className="mt-2 text-2xl font-semibold">{data?.title_ru ?? "MISSION 2 — KPI"}</h1>
          <p className="mt-1 text-sm text-genesis-muted">{data?.subtitle_ru}</p>
        </header>

        {data?.next_action ? <Mission2NextActionCard action={data.next_action} /> : null}

        {data?.metrics ? <Mission2KpiTable metrics={data.metrics} title="Воронка · все этапы" /> : null}

        {data?.training_note_ru ? (
          <p className="text-center text-xs text-genesis-muted">{data.training_note_ru}</p>
        ) : null}
      </div>
    </main>
  );
}
