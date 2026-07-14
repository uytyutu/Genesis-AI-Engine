"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";
import { EngineTaxAccountingPanel } from "./EngineTaxAccountingPanel";
import { EngineDeveloperGuide } from "./EngineDeveloperGuide";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Target = {
  id: string;
  name: string;
  url: string;
  potential_eur: number;
  profit_score: number;
  traffic_band: string;
  abandoned: boolean;
  status: string;
  status_label: string;
  income_rationale: string;
  revenue_eur: number;
  niche: string;
  processing_lane?: string;
  micro_revenue_eur?: number;
};

type Wallet = {
  id: string;
  label: string;
  icon: string;
  connected: boolean;
  balance_label?: string | null;
};

type EngineDash = {
  mode: string;
  system_mode?: string;
  mode_label?: string;
  financial_docs_enabled?: boolean;
  harvest_balance_label?: string;
  potential_revenue?: {
    potential_revenue_eur: number;
    pipeline_potential_eur: number;
    hunter_potential_eur: number;
    active_leads: number;
    high_score_leads: number;
    disclaimer: string;
  };
  realized_revenue?: { realized_revenue_eur: number; revenue_quality: string };
  owner_name: string;
  security_law: string;
  harvest_balance_eur: number;
  lifetime_harvest_eur: number;
  pipeline_potential_eur: number;
  active_assets_count: number;
  available_for_withdrawal_eur: number;
  pending_payouts_eur: number;
  payment_connected: boolean;
  payment_provider_label: string;
  last_sync_at: string | null;
  auto_gate_min_score: number;
  pending_targets: Target[];
  active_assets: Target[];
  harvested_assets?: Target[];
  harvested_count?: number;
  junk_archive_assets?: Target[];
  junk_archive_count?: number;
  junk_micro_revenue_eur?: number;
  network?: {
    mode: string;
    total_assets: number;
    managed_assets: number;
    arbitrage_routes: number;
    mrr_per_asset_eur: number;
    projected_mrr_eur: number;
    target_mrr_eur: number;
    target_progress_percent: number;
    expired_domain_watch: string;
    batch_scan_max: number;
  };
  pattern_intel_value_eur?: number;
  pattern_hits_total?: number;
  hunter?: {
    mode: string;
    zero_cost: boolean;
    priority: string;
    scenario_stats: {
      bounty: number;
      seo_revival: number;
      outreach: number;
      dataset: number;
      outreach_ready: number;
    };
    hunter_value_eur: number;
    dataset_rows: number;
    note: string;
  };
  digital_dust?: {
    recoverable_assets_count: number;
    recoverable_value_eur: number;
    legal_boundary: string;
    etherscan_configured: boolean;
    note: string;
  };
  global_spider?: {
    mode: string;
    zero_cost: boolean;
    regions_enabled: boolean;
    seed_targets_count: number;
    places_configured: boolean;
    note: string;
  };
  places_autopilot?: {
    configured: boolean;
    autopilot_ready: boolean;
    env_var: string;
    primary_config_file: string;
    config_files_found: string[];
    setup_steps: { step: number; title: string; detail: string; url?: string }[];
    free_tier_note: string;
    security_note: string;
    usage: Record<string, string>;
    status_label: string;
  };
  stealth_mode?: {
    enabled: boolean;
    mode: string;
    min_interval_sec: number;
    robots_txt_required: boolean;
    read_only: boolean;
    legal_note: string;
  };
  ai_brain?: {
    configured: boolean;
    brain_ready: boolean;
    recommended_provider: string;
    recommendation_note: string;
    primary_config_file: string;
    active_provider: string | null;
    active_model: string | null;
    env_vars: Record<string, string>;
    status_label: string;
    cold_outreach_note: string;
  };
  smart_gate?: {
    max_risk_score: number;
    min_expected_margin_eur: number;
    auto_executed_count: number;
    manual_review_count: number;
    note: string;
  };
  wallets: Wallet[];
  withdrawal_enabled: boolean;
};

const NICHE_OPTIONS = [
  { id: "local_service", label: "Локальные услуги" },
  { id: "expired_landing", label: "Заброшенные лендинги" },
  { id: "niche_blog", label: "Нишевые блоги" },
];

const TRAFFIC: Record<string, string> = {
  medium: "Средний",
  low: "Низкий",
  trace: "Следы",
};

const WALLET_OPTIONS = [
  { id: "stripe", label: "Stripe" },
  { id: "bank", label: "Банковский счёт" },
  { id: "bitcoin", label: "Bitcoin" },
  { id: "usdt", label: "USDT" },
];

export function EngineDashboard() {
  const [tab, setTab] = useState<"engine" | "tax">("engine");
  const [dash, setDash] = useState<EngineDash | null>(null);
  const [scanUrl, setScanUrl] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawWallet, setWithdrawWallet] = useState("stripe");
  const [connectWallet, setConnectWallet] = useState("stripe");
  const [connectLabel, setConnectLabel] = useState("");
  const [scanNiche, setScanNiche] = useState("local_service");
  const [scanCity, setScanCity] = useState("Berlin");
  const [activateOpen, setActivateOpen] = useState(false);
  const [activatePhrase, setActivatePhrase] = useState("");

  const isSandbox = dash?.system_mode !== "live";
  const placesReady = dash?.places_autopilot?.autopilot_ready ?? dash?.global_spider?.places_configured ?? false;
  const brainReady = dash?.ai_brain?.brain_ready ?? false;

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engine/dashboard`);
      if (res.ok) setDash(await res.json());
    } catch {
      setMessage("Не удалось загрузить Engine Mode. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  async function syncPayments() {
    setBusy("sync");
    try {
      const res = await fetch(`${API}/api/engine/sync-payments`, { method: "POST" });
      const body = await res.json();
      setMessage(
        body.stripe_available_eur != null
          ? `Stripe синхронизирован: ${formatEur(body.stripe_available_eur)}`
          : "Синхронизация завершена",
      );
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runGlobalSpider() {
    setBusy("global");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/global-spider-scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche: scanNiche, batch_limit: 500, tech_pattern_ids: [] }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Global Spider завершён" : "Ошибка"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runNetworkScan() {
    setBusy("network");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/network-scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche: scanNiche, batch_limit: 1000, region: "DE" }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Сетевой поиск завершён" : "Ошибка"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runScanMode() {
    setBusy("scan-mode");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/scan-mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche: scanNiche, city: scanCity, limit: 8 }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Сканирование завершено" : "Ошибка"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runScan(e: React.FormEvent) {
    e.preventDefault();
    if (!scanUrl.trim()) return;
    setBusy("scan");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: scanUrl.trim(), niche: "expired_landing", manual: true }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Сканирование завершено" : "Ошибка"));
      if (res.ok) setScanUrl("");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function acceptTarget(id: string) {
    setBusy(`accept-${id}`);
    try {
      const res = await fetch(`${API}/api/engine/targets/${id}/accept`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Принято");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function connectPayout(e: React.FormEvent) {
    e.preventDefault();
    if (!connectLabel.trim()) return;
    setBusy("connect");
    try {
      const res = await fetch(`${API}/api/engine/wallets/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_id: connectWallet, account_label: connectLabel.trim() }),
      });
      if (res.ok) {
        setMessage("Счёт привязан для вывода");
        setConnectLabel("");
        refresh();
      }
    } finally {
      setBusy("");
    }
  }

  async function withdraw(e: React.FormEvent) {
    e.preventDefault();
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount <= 0) return;
    setBusy("withdraw");
    try {
      const res = await fetch(`${API}/api/engine/withdraw`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_eur: amount, wallet_id: withdrawWallet }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Вывод в очереди" : "Ошибка"));
      if (res.ok) setWithdrawAmount("");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function activateBusiness() {
    setBusy("activate");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/activate-business`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirmed: true,
          phrase: activatePhrase.trim(),
          owner_name: dash?.owner_name ?? "CEO",
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        setMessage("Live Mode активирован — Gewerbe-ready учёт включён");
        setActivateOpen(false);
        setActivatePhrase("");
        refresh();
      } else {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка активации");
      }
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen pb-16">
      <div className="mx-auto max-w-6xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/40 via-genesis-panel to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.4em] text-amber-300/90">Engine Mode</p>
          <h1 className="mt-2 text-3xl font-bold text-white">
            Движок монетизации · {dash?.owner_name ?? "Владелец"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            Сеть активов (PBN/порталы): массовый поиск по Германии, арбитраж трафика на офферы, €20/актив/мес цель.
            Ручной URL или автопилот — одна логика.
          </p>
          {dash?.security_law ? (
            <p className="mt-3 rounded-xl border border-rose-500/30 bg-rose-950/25 px-3 py-2 text-[11px] text-rose-100">
              🔒 {dash.security_law}
            </p>
          ) : null}
          {dash?.stealth_mode?.enabled ? (
            <p className="mt-2 rounded-xl border border-slate-500/30 bg-slate-950/30 px-3 py-2 text-[11px] text-slate-200">
              👻 Stealth Mode · robots.txt · 1 запрос / {dash.stealth_mode.min_interval_sec}s на домен · read-only GET ·{" "}
              {dash.stealth_mode.legal_note}
            </p>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              onClick={() => setTab("engine")}
              className={`rounded-lg border px-3 py-1.5 ${
                tab === "engine"
                  ? "border-amber-500/60 bg-amber-950/40 text-amber-100"
                  : "border-genesis-border hover:bg-genesis-elevated/40"
              }`}
            >
              Движок
            </button>
            <button
              type="button"
              onClick={() => setTab("tax")}
              className={`rounded-lg border px-3 py-1.5 ${
                tab === "tax"
                  ? "border-sky-500/60 bg-sky-950/40 text-sky-100"
                  : "border-genesis-border hover:bg-genesis-elevated/40"
              }`}
            >
              Tax &amp; Accounting
            </button>
            {tab === "engine" ? (
              <button
                type="button"
                disabled={busy === "sync"}
                onClick={() => void syncPayments()}
                className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 text-amber-100 hover:bg-amber-900/40 disabled:opacity-50"
              >
                {busy === "sync" ? "Синхронизация…" : "Синхр. Stripe / API"}
              </button>
            ) : null}
            <Link href="/monitor" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Классический пульт
            </Link>
            <Link href="/finance" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Финансы
            </Link>
          </div>
        </header>

        {tab === "tax" ? (
          <EngineTaxAccountingPanel />
        ) : (
          <>
        {isSandbox ? (
          <section className="rounded-2xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 to-orange-950/30 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-widest text-amber-300">Инкубатор · Sandbox Mode</p>
                <h2 className="mt-1 text-lg font-bold text-white">{dash?.mode_label ?? "Искатель"}</h2>
                <p className="mt-2 max-w-xl text-xs text-amber-100/90">
                  Аналитика рынка без юридических обязательств. Potential Revenue — не реальный доход.
                  Rechnungen и DATEV отключены до Gewerbe.
                </p>
                {dash?.potential_revenue ? (
                  <p className="mt-3 text-2xl font-bold tabular-nums text-emerald-300">
                    Potential: {formatEur(dash.potential_revenue.potential_revenue_eur)}
                    <span className="ml-2 text-xs font-normal text-genesis-muted">
                      · {dash.potential_revenue.active_leads} лидов · {dash.potential_revenue.high_score_leads} сильных
                    </span>
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => setActivateOpen(true)}
                className="rounded-xl bg-red-700 px-6 py-3 text-sm font-bold uppercase tracking-wide text-white shadow-lg hover:bg-red-600"
              >
                ACTIVATE BUSINESS
              </button>
            </div>
          </section>
        ) : (
          <section className="rounded-xl border border-emerald-500/40 bg-emerald-950/25 px-4 py-3 text-sm text-emerald-100">
            Live Mode · Gewerbe-ready · инвойсы и DATEV активны
          </section>
        )}
        {activateOpen ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
            <div className="w-full max-w-md rounded-2xl border border-red-500/50 bg-genesis-panel p-6">
              <h3 className="text-lg font-bold text-white">Активировать бизнес-режим?</h3>
              <p className="mt-2 text-xs text-genesis-muted">
                Только после Gewerbeanmeldung. Включит Rechnungen, DATEV/Lexoffice и налоговые события.
              </p>
              <p className="mt-3 text-xs text-amber-200">
                Введите фразу: <strong>ACTIVATE BUSINESS</strong>
              </p>
              <input
                value={activatePhrase}
                onChange={(e) => setActivatePhrase(e.target.value)}
                className="mt-2 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                placeholder="ACTIVATE BUSINESS"
              />
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  disabled={busy === "activate"}
                  onClick={() => void activateBusiness()}
                  className="flex-1 rounded-xl bg-red-700 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {busy === "activate" ? "Активация…" : "Подтвердить Live Mode"}
                </button>
                <button
                  type="button"
                  onClick={() => setActivateOpen(false)}
                  className="rounded-xl border border-white/20 px-4 py-2.5 text-sm"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        ) : null}
        <EngineDeveloperGuide />
        {dash && (
          <section id="network-kpi" className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Сеть активов · путь к €10 000/мес</h2>
            <p className="mt-1 text-xs text-genesis-muted">
              Управляемых: {dash.network?.managed_assets ?? 0} · арбитраж-маршрутов:{" "}
              {dash.network?.arbitrage_routes ?? 0} · авто-закупка доменов:{" "}
              {dash.network?.expired_domain_watch === "horizon" ? "Horizon" : "—"}
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <Kpi
                label="Прогноз MRR сети"
                value={formatEur(dash.network?.projected_mrr_eur ?? 0)}
                accent
              />
              <Kpi label="Цель MRR" value={formatEur(dash.network?.target_mrr_eur ?? 10_000)} />
              <Kpi
                label="Прогресс к цели"
                value={`${dash.network?.target_progress_percent ?? 0}%`}
              />
            </div>
            <p className="mt-3 text-xs text-violet-200">
              PublicIntelMiner: {dash.pattern_hits_total ?? 0} паттернов · потенциал датасета{" "}
              {formatEur(dash.pattern_intel_value_eur ?? 0)} · режим Hunter-Gatherer (€0 вложений)
            </p>
            {dash.hunter ? (
              <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
                <h3 className="text-xs font-semibold text-emerald-100">
                  Hunter-Gatherer · {dash.hunter.mode} · приоритет {dash.hunter.priority}
                </h3>
                <div className="mt-3 grid gap-2 sm:grid-cols-4 text-[11px]">
                  <div>
                    <span className="text-genesis-muted">Bug Bounty Lite</span>
                    <p className="font-semibold text-white">{dash.hunter.scenario_stats.bounty}</p>
                  </div>
                  <div>
                    <span className="text-genesis-muted">SEO Revival</span>
                    <p className="font-semibold text-white">{dash.hunter.scenario_stats.seo_revival}</p>
                  </div>
                  <div>
                    <span className="text-genesis-muted">Outreach</span>
                    <p className="font-semibold text-white">
                      {dash.hunter.scenario_stats.outreach} · готово {dash.hunter.scenario_stats.outreach_ready}
                    </p>
                  </div>
                  <div>
                    <span className="text-genesis-muted">Датасет</span>
                    <p className="font-semibold text-white">{dash.hunter.dataset_rows} строк</p>
                  </div>
                </div>
                <p className="mt-2 text-[11px] text-emerald-200/80">
                  Потенциал услуг: {formatEur(dash.hunter.hunter_value_eur)} · {dash.hunter.note}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Link
                    href="/acquisition"
                    className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-[11px] text-emerald-100 hover:bg-emerald-900/30"
                  >
                    Очередь Outreach →
                  </Link>
                  <a
                    href={`${API}/api/engine/hunter/dataset.csv`}
                    className="rounded-lg border border-white/15 px-3 py-1.5 text-[11px] text-white/90 hover:bg-white/5"
                  >
                    Скачать датасет CSV
                  </a>
                </div>
              </div>
            ) : null}
            {dash.smart_gate ? (
              <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-950/20 p-4">
                <h3 className="text-xs font-semibold text-amber-100">Smart-Gate · условный авто-апрув</h3>
                <div className="mt-3 grid gap-2 sm:grid-cols-2 text-[11px]">
                  <div>
                    <span className="text-genesis-muted">Auto-Executed</span>
                    <p className="font-semibold text-emerald-300">{dash.smart_gate.auto_executed_count}</p>
                  </div>
                  <div>
                    <span className="text-genesis-muted">Manual Review</span>
                    <p className="font-semibold text-amber-200">{dash.smart_gate.manual_review_count}</p>
                  </div>
                </div>
                <p className="mt-2 text-[11px] text-amber-200/80">
                  Риск ≤ {dash.smart_gate.max_risk_score} · маржа ≥ {formatEur(dash.smart_gate.min_expected_margin_eur)} ·{" "}
                  {dash.smart_gate.note}
                </p>
              </div>
            ) : null}
            {dash.global_spider ? (
              <p className="mt-3 text-[11px] text-sky-200">
                Global Spider: seeds {dash.global_spider.seed_targets_count} · Places{" "}
                {dash.global_spider.places_configured ? "ON" : "OFF"} · {dash.global_spider.note}
              </p>
            ) : null}
            {dash.digital_dust ? (
              <div className="mt-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4">
                <h3 className="text-xs font-semibold text-cyan-100">Digital Dust · Potential Recoverable</h3>
                <p className="mt-1 text-[10px] text-cyan-200/70">{dash.digital_dust.legal_boundary}</p>
                <p className="mt-2 text-[11px]">
                  Активов: <strong>{dash.digital_dust.recoverable_assets_count}</strong> · потенциал{" "}
                  {formatEur(dash.digital_dust.recoverable_value_eur)} · Etherscan{" "}
                  {dash.digital_dust.etherscan_configured ? "ON" : "OFF"}
                </p>
              </div>
            ) : null}
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{ width: `${Math.min(100, dash.network?.target_progress_percent ?? 0)}%` }}
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busy === "network" || !placesReady}
                onClick={() => void runNetworkScan()}
                className="rounded-xl bg-violet-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                title={placesReady ? undefined : "Нужен GOOGLE_PLACES_API_KEY в dashboard/backend/.env.local"}
              >
                {busy === "network" ? "Сканирую Германию…" : "🇩🇪 DE · до 1000 URL"}
              </button>
              <button
                type="button"
                disabled={busy === "global"}
                onClick={() => void runGlobalSpider()}
                className="rounded-xl bg-sky-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy === "global" ? "Global Spider…" : "🕸 Global Spider · весь мир"}
              </button>
            </div>
          </section>
        )}

        {dash && (
          <section id="balance-kpi" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Kpi id="harvest-balance" label={dash.harvest_balance_label ?? "① Баланс добычи"} value={formatEur(dash.harvest_balance_eur)} accent />
            <Kpi label="② Активные активы" value={String(dash.active_assets_count)} />
            <Kpi label="Потенциал воронки" value={formatEur(dash.pipeline_potential_eur)} />
            <Kpi id="withdraw-balance" label="③ К выводу (шлюз)" value={formatEur(dash.available_for_withdrawal_eur)} accent />
            <Kpi label="④ Всего добыто" value={formatEur(dash.lifetime_harvest_eur)} />
          </section>
        )}

        <nav className="flex flex-wrap gap-2 text-[11px] text-genesis-muted">
          <a href="#network-kpi" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Сеть</a>
          <a href="#balance-kpi" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Баланс</a>
          <a href="#scan-mode" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Сканирование</a>
          <a href="#pending-journal" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Журнал</a>
          <a href="#active-assets" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Активные</a>
          <a href="#harvested-assets" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Добытые</a>
          <a href="#junk-archive" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Архив мусора</a>
          <a href="#finance-gateway" className="rounded-full border border-white/10 px-2 py-0.5 hover:text-white">Шлюз</a>
        </nav>

        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            {dash?.places_autopilot && !placesReady ? (
              <section id="places-setup" className="genesis-card border-amber-500/30 bg-amber-950/20 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-sm font-semibold text-amber-100">Откройте «глаза» автопилоту</h2>
                    <p className="mt-1 text-xs text-amber-200/80">
                      Без ключа Genesis не найдёт компании в Google Maps. Это последняя настройка перед автономным поиском.
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-500/20 px-3 py-1 text-[10px] font-medium text-amber-200">
                    Places API OFF
                  </span>
                </div>
                <ol className="mt-4 space-y-3 text-xs text-amber-100/90">
                  {dash.places_autopilot.setup_steps.map((s) => (
                    <li key={s.step} className="flex gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-500/20 text-[11px] font-bold">
                        {s.step}
                      </span>
                      <div>
                        <p className="font-semibold">{s.title}</p>
                        <p className="mt-0.5 text-amber-200/70">{s.detail}</p>
                        {s.url ? (
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-1 inline-block text-amber-300 underline"
                          >
                            Открыть в Google Cloud →
                          </a>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ol>
                <div className="mt-4 rounded-xl border border-amber-500/20 bg-black/20 px-4 py-3 font-mono text-[11px] text-amber-100">
                  <p className="text-amber-200/60">Файл:</p>
                  <p className="mt-1">{dash.places_autopilot.primary_config_file}</p>
                  <p className="mt-2 text-amber-200/60">Строка:</p>
                  <p className="mt-1">{dash.places_autopilot.env_var}=ваш_ключ_из_Google</p>
                </div>
                <p className="mt-3 text-[10px] leading-relaxed text-amber-200/60">
                  {dash.places_autopilot.free_tier_note} {dash.places_autopilot.security_note}
                </p>
              </section>
            ) : null}

            {dash?.places_autopilot?.autopilot_ready ? (
              <p className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-4 py-2 text-xs text-emerald-200">
                ✔ {dash.places_autopilot.status_label} — «Локальные услуги» + город → «Поиск целей» или «DE · до 1000 URL»
              </p>
            ) : null}

            {dash?.ai_brain && !brainReady ? (
              <section className="genesis-card border-violet-500/30 bg-violet-950/20 p-5">
                <h2 className="text-sm font-semibold text-violet-100">Подключите «мозги» ИИ</h2>
                <p className="mt-1 text-xs text-violet-200/80">
                  Без ключа Genesis видит ошибки, но не пишет профессиональный оффер. Рекомендуем{" "}
                  <strong>{dash.ai_brain.recommended_provider.toUpperCase()}</strong> — {dash.ai_brain.recommendation_note}
                </p>
                <div className="mt-4 rounded-xl border border-violet-500/20 bg-black/20 px-4 py-3 font-mono text-[11px] text-violet-100">
                  <p>{dash.ai_brain.primary_config_file}</p>
                  <p className="mt-2">GENESIS_GROQ_API_KEY=gsk_... (или OPENAI_API_KEY=sk-...)</p>
                </div>
                <p className="mt-3 text-[10px] text-violet-200/60">{dash.ai_brain.cold_outreach_note}</p>
              </section>
            ) : null}

            {brainReady ? (
              <p className="rounded-xl border border-violet-500/30 bg-violet-950/20 px-4 py-2 text-xs text-violet-200">
                🧠 {dash?.ai_brain?.status_label} — {dash?.ai_brain?.active_provider} / {dash?.ai_brain?.active_model} · умные офферы и ниши
              </p>
            ) : null}

            <section id="scan-mode" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Поиск целей (автопилот)</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Локальные услуги + город в Германии. Google Places:{" "}
                <strong className={placesReady ? "text-emerald-400" : "text-amber-400"}>
                  {placesReady ? "ON" : "OFF — см. инструкцию выше"}
                </strong>
                .
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <select
                  value={scanNiche}
                  onChange={(e) => setScanNiche(e.target.value)}
                  className="rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                >
                  {NICHE_OPTIONS.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.label}
                    </option>
                  ))}
                </select>
                <input
                  value={scanCity}
                  onChange={(e) => setScanCity(e.target.value)}
                  placeholder="Berlin, Hamburg, München…"
                  className="w-44 rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="button"
                  disabled={busy === "scan-mode"}
                  onClick={() => void runScanMode()}
                  className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  {busy === "scan-mode" ? "Ищу цели…" : "▶ Поиск целей"}
                </button>
              </div>
            </section>

            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Ручной контроль — ваш URL</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Вставьте конкретные ссылки конкурентов или мастерских. Score ≥ {dash?.auto_gate_min_score ?? 45} → журнал;
                ниже → архив мусора с авто-SEO.
              </p>
              <form onSubmit={runScan} className="mt-4 flex gap-2">
                <input
                  required
                  type="url"
                  value={scanUrl}
                  onChange={(e) => setScanUrl(e.target.value)}
                  placeholder="https://заброшенный-актив.de"
                  className="min-w-0 flex-1 rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "scan"}
                  className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  Сканировать
                </button>
              </form>
            </section>

            <section id="pending-journal" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Журнал возможностей — на подтверждение</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Движок уже оценил доходность. Вам остаётся подтвердить перехват.
              </p>
              {!dash?.pending_targets.length ? (
                <p className="mt-4 text-sm text-genesis-muted">Нет целей, прошедших auto-gate. Запустите сканер.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.pending_targets.map((t) => (
                    <TargetCard
                      key={t.id}
                      target={t}
                      busy={busy}
                      onAccept={() => void acceptTarget(t.id)}
                      showAccept
                    />
                  ))}
                </ul>
              )}
            </section>

            <section id="active-assets" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Активные активы (перехвачены)</h2>
              <p className="mt-1 text-xs text-genesis-muted">Перехвачены и в монетизации.</p>
              {!dash?.active_assets.length ? (
                <p className="mt-4 text-sm text-genesis-muted">Пока нет — нажмите «Принять в работу» у цели выше.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.active_assets.map((t) => (
                    <TargetCard key={t.id} target={t} busy={busy} />
                  ))}
                </ul>
              )}
            </section>

            <section id="harvested-assets" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Добытые активы (монетизированы)</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                High-score результат. Счётчик: {dash?.harvested_count ?? 0}
              </p>
              {!dash?.harvested_assets?.length ? (
                <p className="mt-4 text-sm text-genesis-muted">Пока пусто. После монетизации актив появится здесь с суммой добычи.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.harvested_assets.map((t) => (
                    <TargetCard key={t.id} target={t} busy={busy} />
                  ))}
                </ul>
              )}
            </section>

            <section id="junk-archive" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Архив мусора · вторичная обработка</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Low-score активы не удаляются — авто-SEO (meta-теги, описания) даёт микро-доход €0,50–1.
                Всего в архиве: {dash?.junk_archive_count ?? 0} · микро-поток:{" "}
                {formatEur(dash?.junk_micro_revenue_eur ?? 0)}
              </p>
              {!dash?.junk_archive_assets?.length ? (
                <p className="mt-4 text-sm text-genesis-muted">
                  Пусто. Запустите поиск целей или вставьте URL — низкий score попадёт сюда автоматически.
                </p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.junk_archive_assets.map((t) => (
                    <TargetCard key={t.id} target={t} busy={busy} junk />
                  ))}
                </ul>
              )}
            </section>
          </div>

          <aside className="space-y-6">
            <section id="finance-gateway" className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Финансовый шлюз (сердце движка)</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Провайдер: {dash?.payment_provider_label ?? "—"} · синхр. {dash?.last_sync_at ? "активна" : "ожидает"}
              </p>
              <p className="mt-3 text-2xl font-bold text-emerald-300">
                {formatEur(dash?.available_for_withdrawal_eur ?? 0)}
              </p>
              <p className="text-[11px] text-genesis-muted">Доступно к выводу</p>
              {dash?.pending_payouts_eur ? (
                <p className="mt-1 text-xs text-amber-200">В очереди: {formatEur(dash.pending_payouts_eur)}</p>
              ) : null}

              <form onSubmit={connectPayout} className="mt-4 space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs font-medium text-white">Привязать счёт</p>
                <select
                  value={connectWallet}
                  onChange={(e) => setConnectWallet(e.target.value)}
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                >
                  {WALLET_OPTIONS.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.label}
                    </option>
                  ))}
                </select>
                <input
                  value={connectLabel}
                  onChange={(e) => setConnectLabel(e.target.value)}
                  placeholder="IBAN / кошелёк / Stripe account"
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "connect"}
                  className="w-full rounded-lg border border-emerald-500/40 py-2 text-xs text-emerald-100"
                >
                  Привязать
                </button>
              </form>

              <form onSubmit={withdraw} className="mt-4 space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs font-medium text-white">Вывод средств</p>
                <select
                  value={withdrawWallet}
                  onChange={(e) => setWithdrawWallet(e.target.value)}
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                >
                  {(dash?.wallets?.length ? dash.wallets.filter((w) => w.connected) : WALLET_OPTIONS).map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.label}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={1}
                  step={0.01}
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  placeholder="Сумма €"
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "withdraw" || !dash?.withdrawal_enabled}
                  className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
                >
                  {busy === "withdraw" ? "Обработка…" : "Вывести на счёт"}
                </button>
              </form>

              <p className="mt-3 text-[10px] leading-relaxed text-genesis-muted">
                Синхронизация: <code className="text-amber-200/80">monetization_engine_service.py</code> → Stripe Balance API
                (<code>STRIPE_SECRET_KEY</code>) → очередь <code>finance_payouts.jsonl</code>.
              </p>
            </section>

            {message ? (
              <p className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-genesis-muted">{message}</p>
            ) : null}
          </aside>
        </div>
          </>
        )}
      </div>
    </main>
  );
}

function TargetCard({
  target: t,
  busy,
  onAccept,
  showAccept,
  junk,
}: {
  target: Target;
  busy: string;
  onAccept?: () => void;
  showAccept?: boolean;
  junk?: boolean;
}) {
  return (
    <li className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-white">{t.name}</p>
          {t.url ? (
            <a href={t.url} target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-300/90 hover:underline">
              {t.url}
            </a>
          ) : null}
        </div>
        <div className="text-right">
          <p className="font-bold text-emerald-300">{formatEur(t.potential_eur)}</p>
          <p className="text-[10px] text-genesis-muted">score {t.profit_score}</p>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-genesis-muted">
        {TRAFFIC[t.traffic_band] ?? t.traffic_band} · {t.abandoned ? "Заброшен" : "Живой"} · {t.status_label}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-genesis-muted">{t.income_rationale}</p>
      {showAccept ? (
        <button
          type="button"
          disabled={busy === `accept-${t.id}`}
          onClick={onAccept}
          className="mt-3 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
        >
          {busy === `accept-${t.id}` ? "Запуск…" : "Принять в работу"}
        </button>
      ) : null}
      {t.revenue_eur > 0 ? (
        <p className="mt-2 text-sm text-emerald-200">Добыча: {formatEur(t.revenue_eur)}</p>
      ) : null}
      {junk && (t.micro_revenue_eur ?? 0) > 0 ? (
        <p className="mt-1 text-[11px] text-violet-200">
          Микро-SEO: {formatEur(t.micro_revenue_eur ?? 0)} · score {t.profit_score}
        </p>
      ) : null}
    </li>
  );
}

function Kpi({
  label,
  value,
  accent,
  id,
}: {
  label: string;
  value: string;
  accent?: boolean;
  id?: string;
}) {
  return (
    <div
      id={id}
      className={`rounded-xl border p-4 ${
        accent ? "border-amber-500/35 bg-amber-950/20" : "border-genesis-border-subtle bg-genesis-bg/40"
      }`}
    >
      <p className={`text-xl font-bold tabular-nums ${accent ? "text-amber-200" : "text-white"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
