"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Growth = {
  demo_mode: boolean;
  data_source_note: string;
  users_total: number;
  users_growth_percent: number;
  subscriptions_total: number;
  subscriptions_growth_percent: number;
  revenue_growth_percent: number;
  conversion_percent: number;
  conversion_growth_percent: number;
  cac_eur: number;
  cac_change_percent: number;
  retention_percent: number;
  retention_growth_percent: number;
};

export default function GrowthPage() {
  const [data, setData] = useState<Growth | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/growth`);
      setData(await res.json());
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 10000);
    return () => clearInterval(t);
  }, [refresh]);

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-2xl space-y-5">
        <header className="rounded-2xl border border-genesis-border bg-genesis-panel p-6 text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-genesis-muted">Growth Center</p>
          <h1 className="mt-2 text-2xl font-semibold">Рост компании</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Показатели бизнеса — не производства. Рост зависит от ценности продукта, не только от ИИ.
          </p>
          {data?.demo_mode && (
            <span className="mt-3 inline-block rounded-full bg-amber-500/20 px-3 py-1 text-xs text-amber-300">
              Демо-режим
            </span>
          )}
        </header>

        <section className="space-y-3">
          <GrowthRow
            label="Пользователей"
            value={String(data?.users_total ?? 0)}
            change={data?.users_growth_percent}
          />
          <GrowthRow
            label="Подписок"
            value={String(data?.subscriptions_total ?? 0)}
            change={data?.subscriptions_growth_percent}
          />
          <GrowthRow label="Доход" value="—" change={data?.revenue_growth_percent} suffix=" % за период" />
          <GrowthRow
            label="Конверсия"
            value={`${data?.conversion_percent ?? 0} %`}
            change={data?.conversion_growth_percent}
          />
          <GrowthRow
            label="Стоимость привлечения (CAC)"
            value={formatEur(data?.cac_eur)}
            change={data?.cac_change_percent}
            invert
          />
          <GrowthRow
            label="Удержание клиентов"
            value={`${data?.retention_percent ?? 0} %`}
            change={data?.retention_growth_percent}
          />
        </section>

        <p className="rounded-lg border border-dashed border-genesis-border px-4 py-3 text-xs text-genesis-muted">
          {data?.data_source_note}
        </p>

        <div className="flex justify-center gap-4 text-sm">
          <Link href="/" className="text-genesis-accent hover:underline">
            ← Mission Control
          </Link>
          <Link href="/finance" className="text-genesis-accent hover:underline">
            Финансы →
          </Link>
        </div>
      </div>
    </main>
  );
}

function GrowthRow({
  label,
  value,
  change,
  suffix,
  invert,
}: {
  label: string;
  value: string;
  change?: number;
  suffix?: string;
  invert?: boolean;
}) {
  const c = change ?? 0;
  const positive = invert ? c < 0 : c > 0;
  const arrow = c === 0 ? "→" : positive ? "↑" : "↓";
  const color = c === 0 ? "text-genesis-muted" : positive ? "text-emerald-400" : "text-red-400";

  return (
    <div className="rounded-xl border border-genesis-border bg-genesis-panel p-4">
      <div className="flex justify-between gap-4">
        <span className="text-genesis-muted">{label}</span>
        <span className="font-bold">{value}</span>
      </div>
      {c !== 0 && (
        <p className={`mt-1 text-sm ${color}`}>
          {arrow} {Math.abs(c)} %{suffix ?? " за месяц"}
        </p>
      )}
    </div>
  );
}
