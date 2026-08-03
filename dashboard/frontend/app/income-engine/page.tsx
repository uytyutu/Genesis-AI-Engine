"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Opp = {
  id: string;
  title_ru?: string;
  title?: string;
  investment_eur?: number;
  expected_return_eur?: number;
  expected_value_eur?: number;
  confidence?: number;
  risk?: string;
  execution_days?: number;
  reason_ru?: string;
  lane?: string;
  status?: string;
  owner_pitch_ru?: string;
  disclaimer_ru?: string;
};

type ProfitRange = {
  low_eur?: number;
  mid_eur?: number;
  high_eur?: number;
  worst_case_eur?: number;
  best_case_eur?: number;
  confidence_pct?: number;
  display_ru?: string;
  disclaimer_ru?: string;
};

type Evidence = {
  source?: string;
  reasons?: string[];
  confidence_pct?: number;
  display_ru?: string;
};

type Proposal = {
  rank?: number;
  opportunity_id?: string;
  strategy_id?: string;
  title_ru?: string;
  modeled_roi_pct?: number;
  expected_profit?: ProfitRange;
  evidence?: Evidence;
  lifecycle?: string;
  market_discovery?: boolean;
  test_cost_eur?: number;
  pitch_ru?: string;
  paper_trials?: number;
  pipeline_ready_ru?: string;
};

type LabOpportunity = {
  id?: string;
  number?: number;
  title_ru?: string;
  lifecycle?: string;
  evidence?: Evidence;
  expected_profit?: ProfitRange;
  market_discovery?: boolean;
};

type DirectorBrief = {
  found?: number;
  rejected?: number;
  kept?: number;
  expected_profit?: ProfitRange;
  message_ru?: string;
};

type LabBlock = {
  capital_eur?: number;
  active_experiments?: number;
  today?: {
    spent_eur?: number;
    returned_eur?: number;
    net_eur?: number;
    paper_modeled?: number;
  };
  lifetime?: {
    experiments?: number;
    success?: number;
    failed?: number;
    paper_opportunities?: number;
    best_strategy_id?: string | null;
    avg_realized_roi?: number | null;
  };
  search_spend_eur?: number;
};

type Panel = {
  ok?: boolean;
  product_name?: string;
  section?: string;
  law_ru?: string;
  search_law_ru?: string;
  bank_pitch_ru?: string;
  empty_result_ru?: string;
  pitch_template_ru?: string;
  capital?: {
    balance_eur?: number;
    max_experiment_eur?: number;
    suggested_micro_test_eur?: number;
    max_concurrent_experiments?: number;
    reserve_eur?: number;
  };
  auto_approve_limit_eur?: number;
  mission?: {
    status?: string;
    opportunities?: Opp[];
    opportunities_found?: number;
    rejected_count?: number;
    swarm_size?: number;
    result_ru?: string;
    live?: { message_ru?: string; time_remaining_sec?: number };
  } | null;
  alpha_hunter?: {
    stage?: string;
    stage_ru?: string;
    lab_mode?: string;
    analysis_ready?: boolean;
    engine?: string;
    engine_law_ru?: string;
    lab?: LabBlock;
    honesty_ru?: string;
    pipeline?: { id?: string; title_ru?: string }[];
    lifecycle?: string[];
    opportunities?: LabOpportunity[];
    scan?: {
      interval_sec?: number;
      interval_label?: string;
      allowed_sec?: number[];
      allowed_labels?: string[];
      last_scan_at?: string;
      next_scan_at?: string;
      law_ru?: string;
    };
    director?: {
      min_expected_profit_eur?: number;
      min_roi_pct?: number;
      last_brief?: DirectorBrief | null;
      edge_ru?: string;
      role_ru?: string;
    };
    payout?: {
      available_eur?: number;
      message_ru?: string;
      auto_stripe_enabled?: boolean;
      law_ru?: string;
    };
    strategies_ranked?: { id?: string; title_ru?: string; modeled_roi?: number; trials?: number }[];
    venues?: { id?: string; title_ru?: string }[];
    free_sources?: { id?: string; title?: string }[];
    hunters?: { new_market_ru?: string };
    income_layer?: {
      engine?: string;
      engine_law_ru?: string;
      next_r2_ru?: string;
      adapters?: { source_id?: string; name?: string; questions?: Record<string, unknown> }[];
      question_ru?: string;
      money_hunters?: { id?: string; title?: string; title_ru?: string; question_ru?: string }[];
      income_sources?: {
        items?: {
          id: string;
          title: string;
          category: string;
          active?: boolean;
          money_path?: string;
        }[];
        active_count?: number;
        total?: number;
        last_scan?: { message_ru?: string; checked?: number; hits?: number } | null;
      };
      tool_belt?: {
        north_star_ru?: string;
        law_ru?: string;
        counts?: { ready?: number; partial?: number; missing?: number; total?: number };
        checklist?: { id: string; label: string; ok?: boolean }[];
        gaps_ru?: string[];
        tools?: { id: string; title: string; belt: string; status?: string; detail_ru?: string }[];
      };
    };
  };
  safety_ru?: string[];
};

function fmtEur(n: number | undefined | null): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${n.toFixed(2)} €`;
}

export default function IncomeLabPage() {
  const [data, setData] = useState<Panel | null>(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState("");
  const [balance, setBalance] = useState("20");
  const [autoLimit, setAutoLimit] = useState("0.40");
  const [minProfit, setMinProfit] = useState("500");
  const [minRoi, setMinRoi] = useState("30");
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [brief, setBrief] = useState<DirectorBrief | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/income-engine`);
      if (!res.ok) throw new Error("income_engine");
      setData(await res.json());
      setError("");
    } catch {
      setError("Backend недоступен — Genesis.exe (Owner API)");
      setData(null);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 3_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  async function paperDay() {
    setBusy("paper");
    setInfo("");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/paper-day`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          balance_eur: Number(balance) || 20,
          opportunities_target: 100,
        }),
      });
      const json = await res.json();
      setInfo(json.message_ru || "Paper day done · €0 spent");
      setProposals(json.top_strategies || []);
      setBrief(json.director_brief || null);
    } catch {
      setError("Paper day failed");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function proposeTop() {
    setBusy("propose");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/propose-top`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ balance_eur: Number(balance) || 20, n: 3 }),
      });
      const json = await res.json();
      setInfo(json.message_ru || "");
      setProposals(json.proposals || []);
      setBrief(json.director_brief || null);
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function setScanSec(sec: number) {
    setBusy("scan");
    try {
      await fetch(`${API}/api/owner/income-engine/scan-interval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interval_sec: sec }),
      });
      setInfo(`Интервал скана: ${sec / 60}м`);
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function goLive() {
    setBusy("live");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/go-live`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const json = await res.json();
      if (json.ok === false) setError(json.detail_ru || json.error);
      else setInfo(json.message_ru || "LIVE");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function scanIncomeSources() {
    setBusy("sources");
    setInfo("");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/income-sources/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ balance_eur: Number(balance) || 20 }),
      });
      const json = await res.json();
      setInfo(json.message_ru || "Income Sources scanned");
      setBrief(json.director_brief || null);
    } catch {
      setError("Income Sources scan failed");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function toggleSource(sourceId: string, active: boolean) {
    setBusy("tog:" + sourceId);
    try {
      await fetch(`${API}/api/owner/income-engine/income-sources/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_id: sourceId, active }),
      });
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function saveThresholds() {
    setBusy("thr");
    try {
      await fetch(`${API}/api/owner/income-engine/director-thresholds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          min_expected_profit_eur: Number(minProfit) || 500,
          min_roi_pct: Number(minRoi) || 30,
        }),
      });
      setInfo(`Порог директора: ≥ €${minProfit} или ROI ≥ ${minRoi}%`);
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function withdraw() {
    setBusy("wd");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/withdraw`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: true }),
      });
      const json = await res.json();
      if (json.ok === false) setError(json.detail_ru || json.error);
      else setInfo(json.message_ru || "Вывод в очереди Stripe");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function approveMicroTest(strategyId: string) {
    if (!strategyId) return;
    setBusy("micro:" + strategyId);
    setInfo("");
    try {
      const res = await fetch(`${API}/api/owner/income-engine/approve-micro-test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: strategyId,
          balance_eur: Number(balance) || 20,
        }),
      });
      const json = await res.json();
      if (json.ok === false) setError(json.detail_ru || json.error || "approve_failed");
      else setInfo(json.message_ru || "Микро-тест одобрен");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function setStage(stage: string) {
    setBusy("stage");
    try {
      await fetch(`${API}/api/owner/income-engine/stage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage }),
      });
      setInfo(`Stage → ${stage}`);
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function startMission() {
    setBusy("start");
    try {
      await fetch(`${API}/api/owner/income-engine/auto-limit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_approve_limit_eur: Number(autoLimit) || 0 }),
      });
      const res = await fetch(`${API}/api/owner/income-engine/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          balance_eur: Number(balance) || 0,
          auto_approve_limit_eur: Number(autoLimit) || 0,
          simulate_fast: true,
        }),
      });
      const json = await res.json();
      if (json.ok === false) setError(json.detail_ru || json.error);
      else setInfo("Рой охотников сканирует whitelist + free sources (поиск = €0)");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function approve(id: string, mode: "once" | "batch_limit") {
    setBusy(id + mode);
    try {
      const res = await fetch(`${API}/api/owner/income-engine/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity_id: id, mode }),
      });
      const json = await res.json();
      if (json.ok === false) setError(json.detail_ru || json.error);
      else setInfo(json.message_ru || "Одобрено");
    } finally {
      setBusy("");
      void refresh();
    }
  }

  async function reject(id: string) {
    setBusy("rej" + id);
    try {
      await fetch(`${API}/api/owner/income-engine/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity_id: id }),
      });
    } finally {
      setBusy("");
      void refresh();
    }
  }

  const lab = data?.alpha_hunter?.lab;
  const stage = data?.alpha_hunter?.stage || "paper";
  const opps = data?.mission?.opportunities ?? [];
  const life = lab?.lifetime;
  const director = data?.alpha_hunter?.director;
  const payout = data?.alpha_hunter?.payout;
  const scan = data?.alpha_hunter?.scan;
  const labMode = data?.alpha_hunter?.lab_mode || "analysis";
  const analysisReady = !!data?.alpha_hunter?.analysis_ready;
  const labOpps = data?.alpha_hunter?.opportunities ?? [];
  const incomeLayer = data?.alpha_hunter?.income_layer;
  const sources = incomeLayer?.income_sources;
  const toolBelt = incomeLayer?.tool_belt;
  const liveBrief = brief || director?.last_brief || null;
  const avgRoi =
    life?.avg_realized_roi != null
      ? `${(life.avg_realized_roi * 100).toFixed(0)}%`
      : "—";

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 px-4 py-6 md:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="space-y-2">
          <p className="text-[11px] uppercase tracking-wider text-amber-400/90">
            Owner only · Alpha Hunter — Opportunity Discovery Engine
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">
            {data?.alpha_hunter?.engine ?? data?.section ?? "Opportunity Discovery"}
          </h1>
          <p className="text-sm text-zinc-400 max-w-2xl">
            {data?.bank_pitch_ru ??
              "Дай банк. Беру по €0.20–€1 на эксперименты. Успех — масштабирую. Нет — прекращаю."}
          </p>
          <p className="text-xs text-zinc-500 max-w-2xl">
            {data?.search_law_ru}
          </p>
          <div className="flex flex-wrap gap-3 text-xs">
            <Link href="/farm-engine" className="text-violet-300 hover:underline">
              Farm Engine →
            </Link>
            <Link href="/" className="text-zinc-500 hover:underline">
              Mission Control →
            </Link>
          </div>
        </header>

        {error ? (
          <p className="rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-sm">
            {error}
          </p>
        ) : null}
        {info ? (
          <p className="rounded-lg border border-emerald-500/30 bg-emerald-950/30 px-3 py-2 text-sm">
            {info}
          </p>
        ) : null}

        {/* Realistic pipeline + scan cadence */}
        <section className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-2">
          <div className="flex flex-wrap justify-between gap-2">
            <h2 className="text-sm font-medium">Opportunity Discovery · пайплайн</h2>
            <span className="text-[11px] text-amber-200/90">
              Режим: {labMode.toUpperCase()}
              {analysisReady ? " · analysis ready" : " · ждёт анализ"}
            </span>
          </div>
          <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
            {(data?.alpha_hunter?.pipeline ?? []).map((step) => (
              <li key={step.id}>{step.title_ru}</li>
            ))}
          </ol>
          <p className="text-[11px] text-zinc-500">{scan?.law_ru}</p>
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs text-zinc-500">Скан:</span>
            {(scan?.allowed_sec ?? [120, 300, 600, 900, 1800]).map((sec) => (
              <button
                key={sec}
                type="button"
                disabled={!!busy}
                onClick={() => void setScanSec(sec)}
                className={`rounded-md px-2 py-1 text-[11px] border ${
                  scan?.interval_sec === sec
                    ? "border-amber-400/60 bg-amber-500/20"
                    : "border-white/15 hover:bg-white/5"
                }`}
              >
                {sec / 60}м
              </button>
            ))}
            <button
              type="button"
              disabled={!!busy || !analysisReady || labMode === "live"}
              onClick={() => void goLive()}
              className="rounded-md bg-emerald-600/90 px-3 py-1.5 text-xs font-medium disabled:opacity-40"
            >
              → LIVE Income Lab
            </button>
          </div>
          <p className="text-[11px] text-zinc-500">
            {data?.alpha_hunter?.hunters?.new_market_ru ||
              "New Market Hunter: искать новые площадки раньше конкурентов."}
          </p>
        </section>

        {/* Income Sources — where money lives */}
        <section className="rounded-xl border border-sky-500/25 bg-sky-950/15 p-4 space-y-3">
          <h2 className="text-sm font-medium text-sky-100">Income Sources</h2>
          <p className="text-xs text-zinc-400">
            {incomeLayer?.question_ru ||
              "Где сегодня лежат деньги, которые можно заработать законным способом?"}
          </p>
          <div className="flex flex-wrap gap-2 text-[11px] text-zinc-500">
            {(incomeLayer?.money_hunters ?? []).map((h) => (
              <span
                key={h.id}
                className="rounded border border-white/10 px-2 py-1"
                title={h.question_ru}
              >
                {h.title}
              </span>
            ))}
          </div>
          <p className="text-xs text-zinc-400">
            Active: {sources?.active_count ?? 0}/{sources?.total ?? 0}
            {sources?.last_scan?.message_ru
              ? ` · ${sources.last_scan.message_ru}`
              : ""}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5 text-xs max-h-48 overflow-y-auto">
            {(sources?.items ?? []).map((s) => (
              <label
                key={s.id}
                className="flex items-center gap-2 rounded border border-white/10 px-2 py-1.5 cursor-pointer hover:bg-white/5"
              >
                <input
                  type="checkbox"
                  checked={!!s.active}
                  disabled={!!busy}
                  onChange={(e) => void toggleSource(s.id, e.target.checked)}
                />
                <span>
                  {s.title}
                  <span className="block text-[10px] text-zinc-600">{s.category}</span>
                </span>
              </label>
            ))}
          </div>
          <button
            type="button"
            disabled={!!busy}
            onClick={() => void scanIncomeSources()}
            className="rounded-md bg-sky-600/90 px-3 py-2 text-xs font-medium hover:bg-sky-500 disabled:opacity-40"
          >
            Сканировать Income Sources (€0)
          </button>
        </section>

        {/* Tool Belt + Capability Registry */}
        <section className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-3">
          <h2 className="text-sm font-medium">Tool Belt · Capability Registry</h2>
          <p className="text-xs text-zinc-400">{toolBelt?.law_ru}</p>
          <p className="text-xs text-zinc-500">
            Ready {toolBelt?.counts?.ready ?? 0} · Partial {toolBelt?.counts?.partial ?? 0} ·
            Missing {toolBelt?.counts?.missing ?? 0}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-1 text-[11px]">
            {(toolBelt?.checklist ?? []).map((c) => (
              <div
                key={c.id}
                className={`rounded border px-2 py-1 ${
                  c.ok ? "border-emerald-500/30 text-emerald-100/90" : "border-red-500/30 text-red-200/80"
                }`}
              >
                {c.ok ? "✓" : "✗"} {c.label}
              </div>
            ))}
          </div>
          {(toolBelt?.gaps_ru?.length ?? 0) > 0 ? (
            <ul className="text-[11px] text-amber-200/80 space-y-1">
              {(toolBelt?.gaps_ru ?? []).slice(0, 5).map((g) => (
                <li key={g}>· {g}</li>
              ))}
            </ul>
          ) : null}
          {(incomeLayer?.adapters?.length ?? 0) > 0 ? (
            <p className="text-[11px] text-zinc-500">
              Adapters:{" "}
              {(incomeLayer?.adapters ?? []).map((a) => a.name).join(" · ")}
              {incomeLayer?.next_r2_ru ? ` · ${incomeLayer.next_r2_ru}` : ""}
            </p>
          ) : null}
          {data?.alpha_hunter?.engine_law_ru || incomeLayer?.engine_law_ru ? (
            <p className="text-[11px] text-zinc-600">
              {data?.alpha_hunter?.engine_law_ru || incomeLayer?.engine_law_ru}
            </p>
          ) : null}
        </section>

        {liveBrief ? (
          <section className="rounded-xl border border-emerald-500/25 bg-emerald-950/15 p-4 space-y-2">
            <h2 className="text-sm font-medium text-emerald-100">
              Инвестиционный директор
            </h2>
            <p className="text-sm">{liveBrief.message_ru}</p>
            <p className="text-xs text-zinc-400">
              Найдено: {liveBrief.found ?? "—"} · Отклонено: {liveBrief.rejected ?? "—"} ·
              Оставлено: {liveBrief.kept ?? "—"}
              {liveBrief.expected_profit?.display_ru
                ? ` · Expected Profit ${liveBrief.expected_profit.display_ru} (Confidence ${liveBrief.expected_profit.confidence_pct ?? "—"}%)`
                : ""}
            </p>
            <p className="text-[11px] text-zinc-500">{director?.edge_ru}</p>
          </section>
        ) : null}

        {/* Income Lab status board */}
        <section className="rounded-xl border border-amber-500/25 bg-amber-950/15 p-4 space-y-3">
          <h2 className="text-sm font-medium text-amber-100">Income Lab</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
            <div className="rounded-lg border border-white/10 px-3 py-2">
              <p className="text-[11px] text-zinc-500">Капитал</p>
              <p className="font-medium">{fmtEur(lab?.capital_eur ?? Number(balance))}</p>
            </div>
            <div className="rounded-lg border border-white/10 px-3 py-2">
              <p className="text-[11px] text-zinc-500">Активные эксперименты</p>
              <p className="font-medium">{lab?.active_experiments ?? 0}</p>
            </div>
            <div className="rounded-lg border border-white/10 px-3 py-2">
              <p className="text-[11px] text-zinc-500">Сегодня потрачено</p>
              <p className="font-medium">{fmtEur(lab?.today?.spent_eur)}</p>
            </div>
            <div className="rounded-lg border border-white/10 px-3 py-2">
              <p className="text-[11px] text-zinc-500">Чистый результат</p>
              <p className="font-medium">
                {lab?.today?.net_eur != null && lab.today.net_eur >= 0 ? "+" : ""}
                {fmtEur(lab?.today?.net_eur)}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-zinc-400">
            <div>Экспериментов: {life?.experiments ?? 0}</div>
            <div>Успешных: {life?.success ?? 0}</div>
            <div>Неудачных: {life?.failed ?? 0}</div>
            <div>
              Avg ROI: {avgRoi}
              {life?.best_strategy_id ? ` · ${life.best_strategy_id}` : ""}
            </div>
          </div>
          <p className="text-[11px] text-zinc-500">
            Поиск потратил: {fmtEur(lab?.search_spend_eur ?? 0)} (всегда 0) · Макс. эксперимент:{" "}
            {fmtEur(data?.capital?.max_experiment_eur)} (2%) · Параллельно max{" "}
            {data?.capital?.max_concurrent_experiments ?? 10}
          </p>
          <p className="text-xs text-zinc-400">{data?.alpha_hunter?.honesty_ru}</p>
        </section>

        {/* Director thresholds + Stripe desk */}
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
          <h2 className="text-sm font-medium">Порог директора · Stripe</h2>
          <p className="text-xs text-zinc-500">
            Мелочь (€2) не показываем. Только ≥ порога прибыли или ROI.
          </p>
          <div className="flex flex-wrap gap-3 items-end">
            <label className="text-xs text-zinc-400 space-y-1">
              <span>Мин. ожидаемая прибыль (€)</span>
              <input
                value={minProfit}
                onChange={(e) => setMinProfit(e.target.value)}
                className="block w-28 rounded-md border border-white/15 bg-black/40 px-2 py-1.5 text-sm"
              />
            </label>
            <label className="text-xs text-zinc-400 space-y-1">
              <span>Мин. ROI (%)</span>
              <input
                value={minRoi}
                onChange={(e) => setMinRoi(e.target.value)}
                className="block w-24 rounded-md border border-white/15 bg-black/40 px-2 py-1.5 text-sm"
              />
            </label>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void saveThresholds()}
              className="rounded-md border border-white/20 px-3 py-1.5 text-xs hover:bg-white/5 disabled:opacity-40"
            >
              Сохранить порог
            </button>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2 text-sm space-y-1">
            <p className="text-xs text-zinc-500">Payout desk (только realized)</p>
            <p>{payout?.message_ru ?? "Нет подтверждённых выплат."}</p>
            <p className="text-[11px] text-zinc-600">{payout?.law_ru}</p>
            {(payout?.available_eur ?? 0) > 0 ? (
              <button
                type="button"
                disabled={!!busy}
                onClick={() => void withdraw()}
                className="mt-1 rounded-md bg-sky-600/90 px-3 py-1.5 text-xs font-medium hover:bg-sky-500 disabled:opacity-40"
              >
                Вывести {fmtEur(payout?.available_eur)} → Stripe
              </button>
            ) : null}
          </div>
        </section>

        {/* Stages */}
        <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Стадии</h2>
            <span className="text-xs text-amber-200/90">
              {data?.alpha_hunter?.stage_ru ?? stage}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["paper", "1 · Paper (€0)"],
                ["propose", "2 · Propose"],
                ["micro_spend", "3 · Micro spend"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                disabled={!!busy}
                onClick={() => void setStage(id)}
                className={`rounded-md px-3 py-1.5 text-xs border ${
                  stage === id
                    ? "border-amber-400/60 bg-amber-500/20 text-amber-50"
                    : "border-white/15 hover:bg-white/5"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-3 items-end">
            <label className="text-xs text-zinc-400 space-y-1">
              <span>Банк (€)</span>
              <input
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
                className="block w-28 rounded-md border border-white/15 bg-black/40 px-2 py-1.5 text-sm"
              />
            </label>
            <label className="text-xs text-zinc-400 space-y-1">
              <span>Авто-одобрение до (€)</span>
              <input
                value={autoLimit}
                onChange={(e) => setAutoLimit(e.target.value)}
                className="block w-28 rounded-md border border-white/15 bg-black/40 px-2 py-1.5 text-sm"
              />
            </label>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void paperDay()}
              className="rounded-md bg-zinc-100 px-3 py-2 text-xs font-medium text-zinc-900 hover:bg-white disabled:opacity-40"
            >
              Paper day (100 моделей, €0)
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void proposeTop()}
              className="rounded-md border border-amber-400/40 px-3 py-2 text-xs hover:bg-amber-950/40 disabled:opacity-40"
            >
              Propose top 3
            </button>
            <button
              type="button"
              disabled={!!busy}
              onClick={() => void startMission()}
              className="rounded-md bg-amber-500/90 px-3 py-2 text-xs font-medium text-zinc-950 hover:bg-amber-400 disabled:opacity-40"
            >
              Swarm scan
            </button>
          </div>
        </section>

        {labOpps.length > 0 ? (
          <section className="space-y-2">
            <h2 className="text-sm font-medium">
              Opportunities · Lifecycle
            </h2>
            <p className="text-[11px] text-zinc-500">
              {(data?.alpha_hunter?.lifecycle ?? []).join(" → ")}
            </p>
            {labOpps.slice(0, 8).map((o) => (
              <article
                key={o.id}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-3 text-xs space-y-1"
              >
                <div className="flex flex-wrap justify-between gap-2">
                  <p className="font-medium text-sm">
                    Opportunity #{o.number ?? "—"} {o.title_ru}
                    {o.market_discovery ? " · New Market" : ""}
                  </p>
                  <span className="text-amber-200/90">{o.lifecycle}</span>
                </div>
                {o.expected_profit ? (
                  <p>
                    Expected Profit {o.expected_profit.display_ru} · Confidence{" "}
                    {o.expected_profit.confidence_pct}% · Worst{" "}
                    {fmtEur(o.expected_profit.worst_case_eur)} · Best{" "}
                    {fmtEur(o.expected_profit.best_case_eur)}
                  </p>
                ) : null}
                {o.evidence ? (
                  <pre className="whitespace-pre-wrap text-[11px] text-zinc-400 font-sans">
                    {o.evidence.display_ru}
                  </pre>
                ) : null}
              </article>
            ))}
          </section>
        ) : null}

        {proposals.length > 0 ? (
          <section className="space-y-2">
            <h2 className="text-sm font-medium">Предложения (после анализа)</h2>
            {labMode !== "live" ? (
              <p className="text-xs text-amber-200/80">
                Сначала «→ LIVE Income Lab», потом Одобрить.
              </p>
            ) : null}
            {proposals.map((p) => (
              <article
                key={p.strategy_id || String(p.rank)}
                className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-3 text-sm space-y-1"
              >
                <p className="font-medium">
                  #{p.rank ?? "—"} {p.title_ru}
                  {p.lifecycle ? ` · ${p.lifecycle}` : ""}
                </p>
                <p className="text-xs text-zinc-400">{p.pitch_ru}</p>
                {p.expected_profit ? (
                  <p className="text-xs">
                    Expected Profit {p.expected_profit.display_ru} · Confidence{" "}
                    {p.expected_profit.confidence_pct}% · Worst{" "}
                    {fmtEur(p.expected_profit.worst_case_eur)} · Best{" "}
                    {fmtEur(p.expected_profit.best_case_eur)}
                  </p>
                ) : null}
                <p className="text-xs">Тест: {fmtEur(p.test_cost_eur)}</p>
                {p.evidence?.display_ru ? (
                  <pre className="whitespace-pre-wrap text-[11px] text-zinc-500 font-sans">
                    {p.evidence.display_ru}
                  </pre>
                ) : null}
                <button
                  type="button"
                  disabled={!!busy || !p.strategy_id || labMode !== "live"}
                  onClick={() => void approveMicroTest(p.strategy_id || "")}
                  className="mt-1 rounded-md bg-emerald-600/90 px-3 py-1.5 text-xs font-medium hover:bg-emerald-500 disabled:opacity-40"
                >
                  Одобрить {fmtEur(p.test_cost_eur)}
                </button>
              </article>
            ))}
          </section>
        ) : null}

        <section className="space-y-3">
          <h2 className="text-sm font-medium">
            Кандидаты роя ({opps.length})
            {data?.mission?.live?.message_ru ? (
              <span className="ml-2 text-xs font-normal text-zinc-500">
                {data.mission.live.message_ru}
              </span>
            ) : null}
          </h2>
          {opps.length === 0 ? (
            <p className="text-sm text-zinc-500">
              {data?.empty_result_ru ?? "Подходящих сделок не найдено"} — нормальный исход.
              Сначала Paper day.
            </p>
          ) : (
            opps.map((o) => (
              <article
                key={o.id}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-2"
              >
                <h3 className="text-sm font-medium">{o.title_ru || o.title}</h3>
                <p className="text-xs text-amber-100/80">
                  {o.owner_pitch_ru || data?.pitch_template_ru}
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  <div>Эксперимент: {fmtEur(o.investment_eur)}</div>
                  <div>Ожид. возврат: {fmtEur(o.expected_return_eur)}</div>
                  <div>EV: {fmtEur(o.expected_value_eur)}</div>
                  <div>
                    Confidence:{" "}
                    {o.confidence != null ? `${(o.confidence * 100).toFixed(0)}%` : "—"}
                  </div>
                  <div>Срок: {o.execution_days ?? "—"} дн.</div>
                  <div>{o.status}</div>
                </div>
                <p className="text-xs text-zinc-400">{o.reason_ru}</p>
                {(o.status === "proposed" || o.status === "auto_eligible") && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    <button
                      type="button"
                      disabled={!!busy || stage === "paper"}
                      onClick={() => void approve(o.id, "once")}
                      className="rounded-md bg-emerald-600/90 px-3 py-1.5 text-xs font-medium disabled:opacity-40"
                    >
                      Одобрить микро-тест
                    </button>
                    <button
                      type="button"
                      disabled={!!busy || stage === "paper"}
                      onClick={() => void approve(o.id, "batch_limit")}
                      className="rounded-md border border-emerald-500/40 px-3 py-1.5 text-xs disabled:opacity-40"
                    >
                      Все до €{autoLimit}
                    </button>
                    <button
                      type="button"
                      disabled={!!busy}
                      onClick={() => void reject(o.id)}
                      className="rounded-md border border-red-500/40 px-3 py-1.5 text-xs text-red-200 disabled:opacity-40"
                    >
                      Отклонить
                    </button>
                  </div>
                )}
              </article>
            ))
          )}
        </section>

        <section className="rounded-xl border border-white/10 p-4 text-xs text-zinc-500 space-y-2">
          <h2 className="text-sm font-medium text-zinc-300">Whitelist · free sources</h2>
          <p>
            Площадки:{" "}
            {(data?.alpha_hunter?.venues ?? []).map((v) => v.title_ru).join(" · ") || "—"}
          </p>
          <p>
            Поиск (€0):{" "}
            {(data?.alpha_hunter?.free_sources ?? []).map((s) => s.title).join(" · ") || "—"}
          </p>
          <ul className="grid md:grid-cols-2 gap-1">
            {(data?.safety_ru ?? []).map((s) => (
              <li key={s}>· {s}</li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
