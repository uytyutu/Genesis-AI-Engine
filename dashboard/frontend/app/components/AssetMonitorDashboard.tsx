"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Dashboard = {
  targets_found: number;
  in_work: number;
  monetized: number;
  my_income_eur: number;
  pipeline_potential_eur: number;
  security_law: string;
};

type Target = {
  id: string;
  company_name: string;
  website_url?: string;
  fit_reason: string;
  score: number;
  status: string;
  status_label: string;
  potential_value_eur: number;
  revenue_eur?: number;
  notes?: string;
  meta?: {
    niche?: string;
    traffic_band?: string;
    abandoned?: boolean;
    monetization?: string;
  };
  found_at: string;
};

type Niche = { id: string; label: string; default_value_eur: number };

const TRAFFIC_LABEL: Record<string, string> = {
  medium: "Средний",
  low: "Низкий",
  trace: "Следы",
};

const STATUS_TONE: Record<string, string> = {
  new: "border-violet-500/30 bg-violet-950/20",
  reviewed: "border-sky-500/30 bg-sky-950/15",
  proposed: "border-amber-500/35 bg-amber-950/20",
  won: "border-emerald-500/35 bg-emerald-950/20",
};

export function AssetMonitorDashboard() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [targets, setTargets] = useState<Target[]>([]);
  const [niches, setNiches] = useState<Niche[]>([]);
  const [scanUrl, setScanUrl] = useState("");
  const [scanNiche, setScanNiche] = useState("local_service");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [d, t, n] = await Promise.all([
        fetch(`${API}/api/scanner/dashboard`),
        fetch(`${API}/api/scanner/targets?limit=50`),
        fetch(`${API}/api/scanner/niches`),
      ]);
      if (d.ok) setDash(await d.json());
      if (t.ok) {
        const body = await t.json();
        setTargets(body.targets ?? []);
      }
      if (n.ok) {
        const body = await n.json();
        setNiches(body.niches ?? []);
      }
    } catch {
      setMessage("Не удалось загрузить панель. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function runScan(e: React.FormEvent) {
    e.preventDefault();
    const url = scanUrl.trim();
    if (!url) return;
    setBusy("scan");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/scanner/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, niche: scanNiche }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Сканирование отклонено");
        return;
      }
      setMessage(body.message ?? "Цель найдена");
      setScanUrl("");
      refresh();
    } catch {
      setMessage("Ошибка сети");
    } finally {
      setBusy("");
    }
  }

  async function analyze(id: string) {
    setBusy(id);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/scanner/targets/${id}/analyze`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Анализ готов" : "Ошибка"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function acceptWork(id: string) {
    setBusy(`accept-${id}`);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/scanner/targets/${id}/accept`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "В работе" : "Ошибка"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/35 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">Virtus Core · Сканер активов</p>
          <h1 className="mt-2 text-2xl font-semibold text-white">Панель мониторинга</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Журнал возможностей — заброшенные публичные ресурсы с потенциалом дохода. Только легальный asset flipping.
          </p>
          {dash?.security_law ? (
            <p className="mt-3 rounded-xl border border-rose-500/25 bg-rose-950/20 px-3 py-2 text-[11px] text-rose-100/90">
              🔒 {dash.security_law}
            </p>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/acquisition" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Acquisition Studio
            </Link>
            <Link href="/" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Mission Control
            </Link>
          </div>
        </header>

        {dash && (
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Kpi label="Найдено целей" value={String(dash.targets_found)} />
            <Kpi label="В работе" value={String(dash.in_work)} />
            <Kpi label="Монетизировано" value={String(dash.monetized)} />
            <Kpi label="Мой доход" value={formatEur(dash.my_income_eur)} accent />
            <Kpi label="Потенциал воронки" value={formatEur(dash.pipeline_potential_eur)} />
          </section>
        )}

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Сканировать публичный URL</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            Вставьте адрес заброшенного сайта — система оценит трафик, нишу и потенциал дохода.
          </p>
          <form onSubmit={runScan} className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input
              required
              type="url"
              placeholder="https://beispiel-veraltet.de"
              value={scanUrl}
              onChange={(e) => setScanUrl(e.target.value)}
              className="min-w-0 flex-1 rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2.5 text-sm"
            />
            <select
              value={scanNiche}
              onChange={(e) => setScanNiche(e.target.value)}
              className="rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2.5 text-sm"
            >
              {niches.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.label}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={busy === "scan"}
              className="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy === "scan" ? "Сканирую…" : "Найти цель"}
            </button>
          </form>
          {message ? <p className="mt-3 text-xs text-genesis-muted">{message}</p> : null}
        </section>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Журнал возможностей</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            Каждая строка — потенциальный доход с кратким обоснованием. «Принять в работу» запускает монетизацию.
          </p>

          {targets.length === 0 ? (
            <p className="mt-6 rounded-xl border border-dashed border-white/15 px-4 py-8 text-center text-sm text-genesis-muted">
              Пока пусто. Отсканируйте первый публичный URL выше — появится цель с оценкой дохода.
            </p>
          ) : (
            <ul className="mt-5 space-y-4">
              {targets.map((t) => {
                const tone = STATUS_TONE[t.status] ?? "border-white/10 bg-white/[0.02]";
                const traffic = TRAFFIC_LABEL[t.meta?.traffic_band ?? ""] ?? "—";
                const niche = niches.find((n) => n.id === t.meta?.niche)?.label ?? "Актив";
                return (
                  <li key={t.id} className={`rounded-2xl border p-4 ${tone}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-lg font-semibold text-white">{t.company_name}</p>
                        {t.website_url ? (
                          <a
                            href={t.website_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-0.5 block truncate text-xs text-emerald-300/90 hover:underline"
                          >
                            {t.website_url}
                          </a>
                        ) : null}
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold tabular-nums text-emerald-300">
                          {formatEur(t.potential_value_eur)}
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-genesis-muted">потенциал</p>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                      <Badge>{niche}</Badge>
                      <Badge>Трафик: {traffic}</Badge>
                      <Badge>{t.meta?.abandoned ? "Заброшен" : "Живой"}</Badge>
                      <Badge>Score {t.score}</Badge>
                      <Badge>{t.status_label}</Badge>
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-genesis-muted">{t.fit_reason}</p>

                    {Number(t.revenue_eur) > 0 ? (
                      <p className="mt-2 text-sm font-medium text-emerald-200">
                        Зафиксированный доход: {formatEur(Number(t.revenue_eur))}
                      </p>
                    ) : null}

                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={busy === t.id}
                        onClick={() => analyze(t.id)}
                        className="rounded-lg border border-sky-500/40 bg-sky-950/30 px-3 py-1.5 text-xs font-medium text-sky-100 hover:bg-sky-900/40 disabled:opacity-50"
                      >
                        {busy === t.id ? "Анализ…" : "Анализ потенциала"}
                      </button>
                      <button
                        type="button"
                        disabled={busy === `accept-${t.id}` || t.status === "proposed" || t.status === "won"}
                        onClick={() => acceptWork(t.id)}
                        className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                      >
                        {busy === `accept-${t.id}`
                          ? "Запуск…"
                          : t.status === "proposed"
                            ? "В работе"
                            : "Принять в работу"}
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        accent ? "border-emerald-500/35 bg-emerald-950/25" : "border-genesis-border-subtle bg-genesis-bg/40"
      }`}
    >
      <p className={`text-xl font-bold tabular-nums ${accent ? "text-emerald-300" : "text-white"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-genesis-muted">{children}</span>
  );
}
