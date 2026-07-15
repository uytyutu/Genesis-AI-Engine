"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Mission2ConversionPanel,
  Mission2NavGrid,
  Mission2NextActionCard,
  type Mission2KpiData,
} from "../components/Mission2Kpi";
import { MissionProofPanel, type MissionProofData } from "../components/MissionProofPanel";
import { RevenueEnginesPanel, type RevenueEnginesData } from "../components/RevenueEnginesPanel";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function BusinessHealthPage() {
  const [kpi, setKpi] = useState<Mission2KpiData | null>(null);
  const [proof, setProof] = useState<MissionProofData | null>(null);
  const [engines, setEngines] = useState<RevenueEnginesData | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/business-health`);
      if (res.ok) {
        const body = await res.json();
        setKpi(body.mission2_kpi ?? null);
        setProof(body.mission_proof ?? null);
        setEngines(body.revenue_engines ?? null);
      }
    } catch {
      setKpi(null);
      setProof(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = setInterval(refresh, 20000);
    return () => clearInterval(t);
  }, [refresh]);

  const prepareNow = async () => {
    setBusy("prepare");
    setMsg("");
    try {
      const res = await fetch(`${API}/api/acquisition/auto-prepare-discovery`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 3 }),
      });
      const body = await res.json();
      setMsg(body.message_ru ?? "Готово");
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 via-genesis-panel to-genesis-bg p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold">Business Health</h1>
          <p className="mt-2 text-sm text-genesis-muted">Mission 2 — операционная панель · не учебный 121 €</p>
        </header>

        {proof ? <MissionProofPanel data={proof} /> : null}

        {engines ? <RevenueEnginesPanel data={engines} /> : null}

        {kpi?.next_action ? <Mission2NextActionCard action={kpi.next_action} /> : null}

        {kpi?.nav_sections ? (
          <section className="space-y-3">
            <h2 className="text-sm font-medium uppercase tracking-wider text-genesis-muted">Разделы</h2>
            <Mission2NavGrid sections={kpi.nav_sections} />
          </section>
        ) : null}

        <section className="rounded-2xl border border-white/10 bg-genesis-bg/30 p-5">
          <h2 className="text-sm font-medium text-white">Быстрые действия</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => void prepareNow()}
              className="rounded-lg border border-white/15 px-3 py-1.5 text-sm hover:bg-white/5 disabled:opacity-50"
            >
              {busy === "prepare" ? "…" : "Подготовить лиды"}
            </button>
            <Link
              href="/acquisition"
              className="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-500"
            >
              CEO Outbox →
            </Link>
          </div>
          {msg ? <p className="mt-3 text-sm text-emerald-300">{msg}</p> : null}
        </section>

        {kpi ? (
          <Mission2ConversionPanel conversions={kpi.conversions} bottleneck={kpi.bottleneck_ru} />
        ) : null}

        {kpi?.training_note_ru ? (
          <p className="text-center text-xs text-genesis-muted">{kpi.training_note_ru}</p>
        ) : null}
      </div>
    </main>
  );
}
