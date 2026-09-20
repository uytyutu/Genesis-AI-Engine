"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ORACLE = process.env.NEXT_PUBLIC_ORACLE_URL || "http://127.0.0.1:4173";

type CeoDash = {
  virtus?: {
    revenue_eur?: number;
    mrr_eur?: number;
    first_clients?: { count?: number };
    websites_sold?: number;
    ai_stores_sold?: number;
    bots_sold?: number;
  };
  site_funnel?: { visits?: number; paid?: number };
};

type OracleToday = {
  registrations?: number;
  visitors?: number;
  oracleReadings?: number;
  virtSpent?: number;
  virtGifted?: number;
  activeUsers?: number;
  purchases?: number;
};

export default function MissionControlOverview() {
  const [data, setData] = useState<CeoDash | null>(null);
  const [oracle, setOracle] = useState<OracleToday | null>(null);
  const [oracleUsers, setOracleUsers] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setErr("");
    try {
      const res = await fetch(`${API}/api/owner/ceo-dashboard`, { cache: "no-store" });
      const body = await res.json();
      setData(body);
    } catch {
      setErr("CEO API недоступен.");
    }
    const key = typeof window !== "undefined" ? sessionStorage.getItem("ORACLE_OWNER_KEY") : "";
    if (key) {
      try {
        const res = await fetch(`${ORACLE}/oracle/owner`, { headers: { "x-oracle-owner": key } });
        const body = await res.json();
        if (!body.error) {
          setOracle(body.dashboard?.today || {});
          setOracleUsers((body.users || []).length);
        }
      } catch {
        setOracle(null);
      }
    }
    setBusy(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const v = data?.virtus;
  const revenue = Number(v?.revenue_eur || 0);
  const orders = Number(v?.websites_sold || 0) + Number(v?.ai_stores_sold || 0) + Number(v?.bots_sold || 0);
  const customers = Number(v?.first_clients?.count || 0);
  const leads = Number(data?.site_funnel?.visits || 0);
  const mrr = Number(v?.mrr_eur || 0);

  const today: string[] = [];
  if (oracle?.registrations) today.push(`${oracle.registrations} новых Oracle-регистрации`);
  if (oracle?.oracleReadings) today.push(`${oracle.oracleReadings} Oracle-расклада завершены`);
  if (oracle?.purchases) today.push(`${oracle.purchases} Oracle-покупки монет`);

  const kpis = [
    { label: "REVENUE", value: `${revenue} €`, href: "/executive/sales" },
    { label: "ORDERS", value: String(orders), href: "/executive/orders" },
    { label: "CUSTOMERS", value: String(customers), href: "/executive/customers" },
    { label: "NEW LEADS", value: String(leads), href: "/executive/leads" },
    { label: "MRR", value: `${mrr} €`, href: "/executive/sales" },
    { label: "ORACLE USERS", value: String(oracleUsers), href: "/executive/oracle/users" },
  ];

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-8 text-zinc-100">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-zinc-500">Virtus Core</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Mission Control</h1>
          <p className="mt-1 text-sm text-zinc-400">Всё важное о Virtus — деньги, клиенты, продажи и продукты.</p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void load()}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
        >
          Обновить
        </button>
      </header>

      {err ? <p className="text-sm text-rose-200">{err}</p> : null}

      <section className="grid gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {kpis.map((kpi) => (
          <Link
            key={kpi.label}
            href={kpi.href}
            className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 hover:bg-white/5"
          >
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">{kpi.label}</p>
            <p className="mt-1 text-xl text-white">{kpi.value}</p>
          </Link>
        ))}
      </section>

      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <h2 className="text-sm font-semibold text-white">TODAY</h2>
        {today.length ? (
          <ul className="mt-3 space-y-2 text-sm text-zinc-200">
            {today.map((item) => (
              <li key={item}>○ {item}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-zinc-400">На сегодня нет критических действий.</p>
        )}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["Сайты", v?.websites_sold || 0, "/executive/products/websites"],
          ["Магазины", v?.ai_stores_sold || 0, "/executive/products/stores"],
          ["AI-Боты", v?.bots_sold || 0, "/executive/products/bots"],
          ["Virtus Oracle", oracleUsers, "/executive/oracle"],
        ].map(([label, value, href]) => (
          <Link key={String(label)} href={String(href)} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/5">
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</p>
            <p className="mt-2 text-2xl text-white">{value}</p>
            <p className="mt-2 text-xs text-zinc-500">Open →</p>
          </Link>
        ))}
      </section>
    </main>
  );
}
