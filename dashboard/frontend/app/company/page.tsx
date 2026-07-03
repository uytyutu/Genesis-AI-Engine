"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PulseMetric = {
  id: string;
  icon: string;
  label: string;
  count: number;
  href: string | null;
};

type MorningLine = { text: string; highlight: boolean };

type Company = {
  owner_name: string;
  greeting: string;
  company_name: string;
  revenue_today_eur: number;
  revenue_month_eur: number;
  net_profit_eur: number;
  payment_connected: boolean;
  payment_provider_label: string;
  data_source_note: string;
  ceo_note: string;
  pulse: { metrics: PulseMetric[] };
  morning_brief: {
    headline: string;
    owner_greeting: string;
    lines: MorningLine[];
    decisions_needed: number;
  };
};

export default function CompanyPage() {
  const [data, setData] = useState<Company | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/company`);
      setData(await res.json());
    } catch {
      setData(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, [refresh]);

  const brief = data?.morning_brief;
  const metrics = data?.pulse.metrics ?? [];

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-2xl space-y-5">
        <header className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/20 via-genesis-panel to-genesis-bg p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-400/80">Genesis Company</p>
          <h1 className="mt-2 text-2xl font-semibold">{data?.company_name ?? "Genesis Company"}</h1>
          {brief && (
            <>
              <p className="mt-4 text-lg font-medium">{brief.headline}</p>
              <p className="mt-1 text-sm text-genesis-muted">{brief.owner_greeting}</p>
              <div className="mt-5 rounded-xl border border-white/5 bg-genesis-bg/50 p-4">
                <p className="text-xs uppercase tracking-wider text-genesis-muted">За ночь и сегодня</p>
                <ul className="mt-3 space-y-2 text-sm">
                  {brief.lines.map((line) => (
                    <li
                      key={line.text}
                      className={line.highlight ? "font-medium text-emerald-300" : "text-genesis-muted"}
                    >
                      {line.text}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </header>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Компания сейчас</h2>
          <p className="mt-1 text-xs text-genesis-muted">Язык владельца — не названия движков</p>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {metrics.map((m) => {
              const inner = (
                <div className="flex items-center justify-between gap-3 rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 px-4 py-3">
                  <span className="text-sm">
                    {m.icon} {m.label}
                  </span>
                  <span className="text-xl font-bold tabular-nums">{m.count}</span>
                </div>
              );
              return m.href ? (
                <Link key={m.id} href={m.href} className="transition hover:opacity-90">
                  {inner}
                </Link>
              ) : (
                <div key={m.id}>{inner}</div>
              );
            })}
          </div>
        </section>

        <section className="grid grid-cols-2 gap-3">
          <FinanceTile label="Доход сегодня" value={formatEur(data?.revenue_today_eur)} />
          <FinanceTile label="Доход за месяц" value={formatEur(data?.revenue_month_eur)} />
          <FinanceTile label="Чистая прибыль" value={formatEur(data?.net_profit_eur)} highlight />
          <FinanceTile
            label="Оплата"
            value={data?.payment_connected ? data.payment_provider_label : "Не подключена"}
          />
        </section>

        {brief && brief.decisions_needed > 0 && (
          <section className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-5">
            <p className="text-sm font-medium text-amber-200">
              Требуется ваше решение: {brief.decisions_needed}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link
                href="/"
                className="rounded-lg bg-amber-500/20 px-3 py-1.5 text-xs font-medium text-amber-100"
              >
                Заявки и оплаты
              </Link>
              <Link
                href="/opportunities"
                className="rounded-lg border border-amber-500/30 px-3 py-1.5 text-xs text-amber-100/90"
              >
                Журнал возможностей
              </Link>
            </div>
          </section>
        )}

        <section className="rounded-xl border border-genesis-border bg-genesis-panel/60 p-5 text-sm">
          <p className="text-genesis-muted">{data?.ceo_note}</p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs">
            <Link href="/finance" className="text-genesis-accent hover:underline">
              Финансы →
            </Link>
            <Link href="/launch" className="text-genesis-accent hover:underline">
              Public Launch →
            </Link>
            <Link href="/site" className="text-genesis-accent hover:underline">
              Публичная страница →
            </Link>
            <Link href="/check" className="text-genesis-muted hover:underline">
              Разработчик →
            </Link>
          </div>
        </section>

        <p className="text-xs text-genesis-muted">{data?.data_source_note}</p>
      </div>
    </main>
  );
}

function FinanceTile({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string | undefined;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        highlight ? "border-emerald-500/30 bg-emerald-950/10" : "border-genesis-border bg-genesis-panel"
      }`}
    >
      <p className="text-xs text-genesis-muted">{label}</p>
      <p className="mt-1 text-lg font-bold">{value ?? "—"}</p>
    </div>
  );
}
