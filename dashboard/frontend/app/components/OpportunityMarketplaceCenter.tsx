"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Farm = {
  id: string;
  label_ru: string;
  stars: number;
  status: string;
  status_ru: string;
  flow_ru?: string[];
  rule_ru?: string;
  href?: string;
  networks?: { id: string; connected: boolean; role: string }[];
  products?: { id: string; enabled?: boolean; path?: string; price_eur?: string }[];
};

type Opp = {
  id: string;
  title_ru: string;
  farm_id: string;
  roi: string;
  priority: number;
  action_ru: string;
  why_ru: string;
  live: boolean;
};

type Board = {
  headline_ru?: string;
  title_ru?: string;
  subtitle_ru?: string;
  principle_ru?: string;
  digital_farm_note_ru?: string;
  external_task_marketplace?: boolean;
  farms?: Farm[];
  opportunities?: Opp[];
  desk_pulse?: {
    ready_now?: number;
    waiting?: number;
    autosend?: boolean;
    runner?: boolean;
    sent_today?: number;
    stripe_key?: boolean;
    digistore_key?: boolean;
  };
};

function roiTone(roi: string): string {
  if (roi === "high") return "border-emerald-500/40 bg-emerald-950/25 text-emerald-100";
  if (roi === "medium") return "border-amber-500/35 bg-amber-950/20 text-amber-50";
  return "border-white/10 bg-black/20 text-white/80";
}

function statusPill(status: string): string {
  if (status === "live") return "border-emerald-400/40 text-emerald-200";
  if (status === "partial" || status === "own_orders_only") return "border-sky-400/40 text-sky-200";
  return "border-white/20 text-white/50";
}

export function OpportunityMarketplaceCenter() {
  const [board, setBoard] = useState<Board | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/earn-marketplace/today`);
      if (!res.ok) {
        setErr(`Marketplace ${res.status} — перезапустите Genesis`);
        return;
      }
      setBoard(await res.json());
      setErr("");
    } catch {
      setErr("Backend недоступен");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pulse = board?.desk_pulse;
  const opps = board?.opportunities ?? [];
  const farms = board?.farms ?? [];

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-6 sm:px-6">
        <header className="rounded-2xl border border-violet-500/30 bg-gradient-to-br from-violet-950/40 via-genesis-panel to-genesis-bg p-6 sm:p-8">
          <p className="text-xs uppercase tracking-[0.35em] text-violet-300/80">{BRAND_NAME}</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">
            {board?.title_ru ?? "Marketplace возможностей"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            {board?.subtitle_ru ??
              "Реальные способы создать ценность и получить оплату. Не цифровая ферма разметки."}
          </p>
          <p className="mt-3 text-sm font-medium text-violet-100">
            {board?.headline_ru ?? (busy ? "Загрузка…" : "—")}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10"
            >
              Обновить сегодня
            </button>
            <Link
              href="/revenue"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Доход / Work Farm →
            </Link>
            <Link
              href="/acquisition"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Country Desk →
            </Link>
            <Link
              href="/"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm text-genesis-muted hover:text-white"
            >
              Ферма разметки (другое) →
            </Link>
          </div>
          {err ? <p className="mt-3 text-xs text-amber-200">{err}</p> : null}
          {board?.digital_farm_note_ru ? (
            <p className="mt-3 text-[11px] text-white/40">{board.digital_farm_note_ru}</p>
          ) : null}
        </header>

        {pulse ? (
          <section className="grid gap-2 sm:grid-cols-4">
            <Pulse label="Ready" value={String(pulse.ready_now ?? 0)} />
            <Pulse label="Waiting" value={String(pulse.waiting ?? 0)} />
            <Pulse label="Sent today" value={String(pulse.sent_today ?? 0)} />
            <Pulse
              label="Ключи"
              value={`Stripe ${pulse.stripe_key ? "✓" : "—"} · Digi ${pulse.digistore_key ? "✓" : "—"}`}
            />
          </section>
        ) : null}

        <section className="rounded-2xl border border-emerald-500/25 bg-emerald-950/15 p-5">
          <h2 className="text-sm font-semibold text-emerald-100">Сегодня найдено</h2>
          <p className="mt-1 text-[11px] text-genesis-muted">
            Список возможностей с ROI — делать живые (live) в первую очередь.
          </p>
          <ol className="mt-4 space-y-3">
            {opps.map((o, idx) => (
              <li
                key={o.id}
                className={`rounded-xl border px-4 py-3 text-sm ${roiTone(o.roi)}`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium text-white">
                    <span className="mr-2 text-white/40">{idx + 1}.</span>
                    {o.title_ru}
                  </p>
                  <div className="flex gap-2 text-[10px] uppercase">
                    <span className="rounded-full border border-white/20 px-2 py-0.5">
                      ROI {o.roi}
                    </span>
                    <span
                      className={`rounded-full border px-2 py-0.5 ${
                        o.live
                          ? "border-emerald-400/40 text-emerald-200"
                          : "border-white/15 text-white/45"
                      }`}
                    >
                      {o.live ? "live" : "plan"}
                    </span>
                  </div>
                </div>
                <p className="mt-2 text-xs text-white/85">→ {o.action_ru}</p>
                <p className="mt-1 text-[11px] text-white/50">{o.why_ru}</p>
                <p className="mt-1 font-mono text-[10px] text-violet-200/70">{o.farm_id}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-white">Пять ферм ценности</h2>
          <div className="grid gap-3 lg:grid-cols-2">
            {farms.map((f) => (
              <article
                key={f.id}
                className="rounded-2xl border border-white/10 bg-black/25 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-white">
                    {"★".repeat(Math.min(5, f.stars))} {f.label_ru}
                  </h3>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] uppercase ${statusPill(f.status)}`}
                  >
                    {f.status}
                  </span>
                </div>
                <p className="mt-2 text-xs text-genesis-muted">{f.status_ru}</p>
                {f.flow_ru?.length ? (
                  <p className="mt-2 text-[11px] text-violet-100/75">{f.flow_ru.join(" → ")}</p>
                ) : null}
                {f.networks?.length ? (
                  <ul className="mt-2 flex flex-wrap gap-1.5 text-[10px]">
                    {f.networks.map((n) => (
                      <li
                        key={n.id}
                        className={`rounded border px-2 py-0.5 ${
                          n.connected
                            ? "border-emerald-500/40 text-emerald-200"
                            : "border-white/10 text-white/40"
                        }`}
                      >
                        {n.id}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {f.products?.length ? (
                  <ul className="mt-2 space-y-1 text-[11px] text-genesis-muted">
                    {f.products.map((p) => (
                      <li key={p.id}>
                        {p.enabled ? "✓" : "○"} {p.id}
                        {p.path ? ` · ${p.path}` : ""}
                        {p.price_eur ? ` · ${p.price_eur}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <p className="mt-2 text-[10px] text-white/40">{f.rule_ru}</p>
                {f.href ? (
                  <Link href={f.href} className="mt-3 inline-block text-xs text-violet-300 hover:underline">
                    Открыть →
                  </Link>
                ) : null}
              </article>
            ))}
          </div>
        </section>

        {board?.principle_ru ? (
          <p className="text-center text-xs text-genesis-muted">{board.principle_ru}</p>
        ) : null}
        <p className="text-center text-[10px] text-white/30">
          external_task_marketplace = {String(board?.external_task_marketplace ?? false)}
        </p>
      </div>
    </main>
  );
}

function Pulse({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-2">
      <p className="text-[10px] uppercase text-white/45">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums text-white">{value}</p>
    </div>
  );
}
