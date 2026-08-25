"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../lib/publicBrand";
import { fetchApi } from "../lib/fetchApi";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Pulse = {
  clients: number | null;
  ordersNew: number | null;
  inProduction: number | null;
  revenueEur: number | null;
  supportOpen: number | null;
  systemOk: boolean | null;
};

/**
 * Clean Owner Overview — коммерческий пульс Virtus.
 * Без Farm / Toloka / API Farm / Money Hunter.
 */
export function OwnerOverview() {
  const [pulse, setPulse] = useState<Pulse>({
    clients: null,
    ordersNew: null,
    inProduction: null,
    revenueEur: null,
    supportOpen: null,
    systemOk: null,
  });
  const [busy, setBusy] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const [dashRes, ordersRes, supportRes, checkRes] = await Promise.all([
        fetchApi(`${API}/api/owner/ceo-dashboard`, { timeoutMs: 12_000 }),
        fetchApi(`${API}/api/sales/orders`, { timeoutMs: 10_000 }),
        fetchApi(`${API}/api/support/threads?limit=80`, { timeoutMs: 8_000 }),
        fetchApi(`${API}/api/owner/system-check`, { timeoutMs: 8_000 }),
      ]);

      let clients: number | null = null;
      let revenueEur: number | null = null;
      if (dashRes.ok) {
        const dash = await dashRes.json();
        clients = Number(dash?.virtus?.first_clients?.count ?? null);
        if (Number.isNaN(clients as number)) clients = null;
        const rev = dash?.virtus?.revenue_eur;
        revenueEur = typeof rev === "number" ? rev : null;
      }

      let ordersNew: number | null = null;
      let inProduction: number | null = null;
      if (ordersRes.ok) {
        const body = await ordersRes.json();
        const list = (body.orders || []) as { status?: string }[];
        ordersNew = list.filter((o) =>
          ["pending_confirmation", "confirmed", "awaiting_payment"].includes(
            String(o.status || ""),
          ),
        ).length;
        inProduction = list.filter((o) =>
          ["paid", "in_production", "ready"].includes(String(o.status || "")),
        ).length;
      }

      let supportOpen: number | null = null;
      if (supportRes.ok) {
        const body = await supportRes.json();
        const items = body.items || body.threads || [];
        supportOpen = Array.isArray(items) ? items.length : 0;
      }

      let systemOk: boolean | null = null;
      if (checkRes.ok) {
        const body = await checkRes.json();
        systemOk = body?.ok !== false && body?.ready !== false;
      }

      setPulse({
        clients,
        ordersNew,
        inProduction,
        revenueEur,
        supportOpen,
        systemOk,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Не удалось загрузить обзор");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const cards = [
    {
      label: "Пользователи",
      value: pulse.clients != null ? String(pulse.clients) : "—",
      hint: "зарегистрировано",
      href: "/users",
    },
    {
      label: "Заказы",
      value: pulse.ordersNew != null ? String(pulse.ordersNew) : "—",
      hint: "ждут действия",
      href: "/orders",
    },
    {
      label: "Выручка",
      value:
        pulse.revenueEur != null ? formatEur(pulse.revenueEur) : "—",
      hint: "реальные коммерческие €",
      href: "/finance",
    },
    {
      label: "В работе",
      value: pulse.inProduction != null ? String(pulse.inProduction) : "—",
      hint: "производство / готово",
      href: "/factory",
    },
    {
      label: "Поддержка",
      value: pulse.supportOpen != null ? String(pulse.supportOpen) : "—",
      hint: "открытые обращения",
      href: "/support",
    },
    {
      label: "Система",
      value:
        pulse.systemOk == null ? "—" : pulse.systemOk ? "OK" : "Проверить",
      hint: "здоровье платформы",
      href: "/check",
    },
  ];

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-4 py-8 text-zinc-100">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            {BRAND_NAME} · Mission Control
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Обзор</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Клиент → заказ → продукт → готово → оплата → поддержка
          </p>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void load()}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
        >
          {busy ? "Обновление…" : "Обновить"}
        </button>
      </header>

      {err ? (
        <p className="rounded-xl border border-rose-400/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-100">
          {err}
        </p>
      ) : null}

      <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/15 p-5">
        <h2 className="text-sm font-semibold text-emerald-100">Сегодня</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {cards.map((c) => (
            <Link
              key={c.label}
              href={c.href}
              className="rounded-xl border border-white/10 bg-black/35 px-4 py-3 transition hover:border-emerald-400/40 hover:bg-black/50"
            >
              <p className="text-[11px] uppercase tracking-wide text-zinc-500">
                {c.label}
              </p>
              <p className="mt-1 text-2xl font-semibold text-white">{c.value}</p>
              <p className="mt-0.5 text-xs text-zinc-400">{c.hint}</p>
            </Link>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
        <h2 className="text-sm font-semibold text-white">Управление</h2>
        <p className="mt-1 text-xs text-zinc-500">
          Только рабочие экраны. Ферма и labs — в «Студии».
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href="/users"
            className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
          >
            Найти клиента
          </Link>
          <Link
            href="/orders"
            className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
          >
            Заказы
          </Link>
          <Link
            href="/factory"
            className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
          >
            Продукты
          </Link>
          <Link
            href="/support"
            className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
          >
            Поддержка
          </Link>
          <Link
            href="/finance"
            className="rounded-xl border border-white/20 px-4 py-2 text-sm font-semibold text-white"
          >
            Финансы
          </Link>
        </div>
      </section>

      <p className="text-[11px] leading-relaxed text-zinc-600">
        Farm Potential, Toloka, API Farm и симуляции не показываются здесь — они
        в Студии → Ферма. На обзоре только коммерческий Virtus Core.
      </p>
    </main>
  );
}
