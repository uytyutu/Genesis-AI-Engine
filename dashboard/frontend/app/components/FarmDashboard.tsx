"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";
import { fetchApi } from "../lib/fetchApi";
import {
  FarmTaskEvent,
  PayoutGuide,
  lifecycleRowClass,
  lifecycleTitle,
  showPayAmount,
  taskTone,
} from "../lib/farmLifecycleUi";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function farmList<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

type Combiner = { id: string; label: string; pay_eur: number; pay_label: string; primary?: boolean };
type Platform = {
  id: string;
  label: string;
  status: string;
  status_label: string;
  note: string;
  env_var?: string;
  pay_hint?: string;
  signup_url?: string | null;
  steps?: string[];
  connected?: boolean;
};
type ChecklistItem = { step: string; title: string; detail: string };
type TaskEvent = FarmTaskEvent;

type FarmDash = {
  owner_name: string;
  running: boolean;
  workers_active: number;
  workers_target: number;
  today_earned_eur: number;
  total_earned_eur: number;
  total_tasks_done: number;
  net_profit_eur: number;
  available_for_withdraw_eur: number;
  withdraw_min_eur: number;
  sandbox: boolean;
  balance_label: string;
  combiners: Combiner[];
  worker_flow?: { step: number; id: string; title: string; detail: string }[];
  primary_combiner?: string;
  async_concurrency?: number;
  platforms: Platform[];
  ceo_checklist?: ChecklistItem[];
  labels_export_count?: number;
  labels_export_ready?: boolean;
  toloka_submit?: {
    configured?: boolean;
    auto_submit_enabled?: boolean;
    connected?: boolean;
    pending_count?: number;
    submitted_count?: number;
    last_submit_at?: string | null;
    last_error?: string | null;
    dataset_id?: string;
    pipeline_id?: string;
    last_run_status?: string;
    circuit_breaker?: {
      safe_mode?: boolean;
      safe_mode_reason?: string;
      seconds_remaining?: number;
    };
    message?: string;
  };
  scale_ai?: {
    connected: boolean;
    configured: boolean;
    status: string;
    status_label: string;
    log_line?: string;
    message?: string;
  };
  priority_manager?: {
    pipeline_parallelism: boolean;
    async_note: string;
    router_note: string;
    cache: { entries: number; max_entries: number };
    learning: {
      total_ops: number;
      min_ops_for_priority: number;
      investor_mode: boolean;
      top_adapter: string | null;
      note: string;
      adapters: { adapter_id: string; eur_per_second: number; cache_rate: number }[];
    };
    cloud_dispatcher?: {
      execution_mode: string;
      local_note: string;
      pool_configured: boolean;
      pool: { ok: boolean; status: string; message: string; pool_url?: string };
    };
  };
  recent_tasks: TaskEvent[];
  honesty_note: string;
  cost_ratio_note: string;
  last_tick_at: string | null;
  revenue_forecast?: {
    disclaimer: string;
    labeling_swarm_10h: { net_eur: number; nodes: number; gross_eur: number };
    labeling_swarm_per_day: { net_eur: number };
    phases: { label: string; eur_per_day: string; note: string }[];
    scaling_note: string;
  };
  last_battle_test?: {
    at: string;
    earned_eur: number;
    tasks_done: number;
    execution_target: string;
    pay_per_task_eur: number;
    tasks_per_hour_est: number;
  };
  prepare_live?: {
    farm_mode: string;
    live_ready: boolean;
    checklist: { step: number; done: boolean; title: string }[];
    next?: string;
  };
  global_spider?: {
    toloka_categories_count: number;
    toloka_task_categories?: string[];
    seed_targets_count?: number;
    seed_targets?: string[];
    places_queries_count: number;
    places_configured: boolean;
    min_task_price?: number;
    polling_interval_sec?: number;
    hunter_mode?: boolean;
    note?: string;
  };
  dry_run?: {
    active: boolean;
    execution_mode: string;
    streak: number;
    milestone_target: number;
    milestone_reached: boolean;
    total_potential_eur: number;
    log_format: string;
    note: string;
    task_selection?: {
      pipeline: { step: number; name: string; detail: string }[];
    };
  };
  payment_monitor?: {
    monitor: {
      farm_mode: string;
      execution_mode?: string;
      scale: {
        connected?: boolean;
        balance_usd: number | null;
        live_tasks: boolean;
        task_count?: number;
        withdraw_note: string;
      };
      toloka: {
        connected?: boolean;
        balance_usd: number | null;
        live_tasks: boolean;
        task_count?: number;
        withdraw_note: string;
      };
    } | null;
    payout: {
      threshold_usd: number;
      has_withdraw_ready?: boolean;
      pending_alerts?: { title: string; message: string; balance_usd: number }[];
      stripe_note?: string;
      auto_payout: boolean;
    } | null;
    note?: string;
    remote_warning?: string;
  };
  last_live_connection_test?: { ok: boolean; log_line?: string; message?: string; at?: string };
  payout_guide?: PayoutGuide;
  first_euro_gate?: {
    verdict: string;
    headline: string;
    core_question: string;
    first_euro_confirmed: boolean;
    verified_revenue_confirmed?: boolean;
    vre_level?: number;
    vre?: {
      level: number;
      level_label_ru: string;
      engine_proven: boolean;
      pipeline_success_count: number;
    };
    auto_steps_done: number;
    auto_steps_total: number;
    ceo_action_now: string;
    steps: {
      id: string;
      title: string;
      detail: string;
      done: boolean;
      kind: "auto" | "manual";
    }[];
    evidence_verdict_ru?: string;
    commercial_evidence?: CommercialEvidence;
    title_ru?: string;
    mission1_freeze?: {
      title_ru: string;
      pr_gate_question_ru?: string;
      pr_gate_rule_ru?: string;
      allowed_ru: string[];
      forbidden_ru: string[];
      until_ru?: string;
    };
    revenue_confidence?: {
      confidence_pct: number;
      label_ru: string;
      note_ru: string;
    };
    channel_review_message_ru?: string | null;
  };
  farm_program?: {
    title_ru: string;
    vre_level: number;
    pr_gate?: { question_ru: string; rule_ru: string; active: boolean };
    pipeline?: { diagram_ru: string; stages: { id: string; title: string; done: boolean }[] };
    post_first_revenue_questions_ru?: string[];
    revenue_path_map?: {
      title_ru: string;
      current_step_ru: string;
      current_money_note_ru: string;
      blocker_ru?: string | null;
      steps: {
        id: string;
        title_ru: string;
        truth_kind: string;
        done: boolean;
        money_ru: string;
      }[];
    };
    truth_engine?: {
      title_ru: string;
      records: { label_ru: string; value: unknown; truth_kind: string; detail_ru?: string }[];
    };
    error_ledger?: {
      total_logged: number;
      hint_ru?: string | null;
      by_taxonomy?: Record<string, number>;
      last_entry?: { taxonomy_ru?: string; message?: string; at?: string };
    };
    explainability?: {
      title_ru: string;
      recommendation_ru: string;
      reasons: string[];
      probabilities?: Record<string, string>;
      next_action_ru?: string;
    };
    force_vectors?: {
      title_ru: string;
      note_ru: string;
      vectors: {
        id: string;
        title_ru: string;
        subtitle_ru: string;
        status_ru: string;
        unlocked: boolean;
        locked_reason_ru?: string | null;
      }[];
    };
    post_vre4_sequence_ru?: string[];
    verified_revenue_status?: "VERIFIED" | "NOT VERIFIED";
    commercial_experiments?: {
      date_ru?: string;
      channel: string;
      outcome_ru: string;
      outcome_code: string;
    }[];
    revenue_replay?: { label_ru?: string; saved_at?: string; steps_ru?: string[] };
  };
  production_platform?: {
    title_ru: string;
    subtitle_ru: string;
    conveyor_status_ru: string;
    toloka_role_ru: string;
    b2b_brief?: {
      tagline_ru: string;
      we_sell_ru: string[];
      problems_we_solve_ru: string[];
      pitch_ru: string;
      packages_ru: { scenario: string; client_says: string; genesis_says: string }[];
      cta_ru: string;
    };
    product_catalog?: {
      service_number: number;
      title_ru: string;
      problem_ru: string;
      price_b2b_eur: number;
      unit_label_ru: string;
      sla_example_ru: string;
    }[];
    capability_marketplace?: { id: string; label_ru: string; ready: boolean }[];
    revenue_router?: {
      channels: {
        id: string;
        label_ru: string;
        potential_ru: string;
        why_ru: string;
        status: string;
      }[];
      recommended_ru: string;
    };
  };
  opportunity_discovery?: {
    title_ru: string;
    subtitle_ru: string;
    tagline_ru?: string;
    cto_warning_ru?: string;
    automation_level_ru?: string;
    mission_formula_ru?: string[];
    ceo_hints_ru?: string[];
    stats?: {
      scanned: number;
      evaluated: number;
      high_win_probability: number;
      pipeline_value_eur: number;
    };
    methods?: { id: string; title_ru: string; summary_ru: string; status_ru: string }[];
    top_opportunities?: {
      opportunity_id: string;
      company_name: string;
      primary_problem_ru?: string;
      opportunity_score_pct?: number;
      win_probability_pct: number;
      confidence_pct?: number;
      confidence_reasons_ru?: string[];
      win_probability_reasons_ru?: string[];
      problems_count: number;
      sell_price_eur: number;
      duration_label_ru?: string;
      service_label_ru?: string;
      proposal_ready?: boolean;
      lifetime_value?: {
        repeat_sale_probability_pct?: number;
        contact_reminder_ru?: string;
      } | null;
      market_memory?: { prior_lost?: number; last_lost_reason_ru?: string | null };
    }[];
    confidence?: {
      confidence_pct: number;
      confidence_reasons_ru: string[];
      honesty_note_ru: string;
      ceo_goal_ru?: string;
    };
    learning_timeline?: {
      title_ru: string;
      hint_ru: string;
      current_conversations: number;
      stages: { milestone: number; title_ru: string; status: string; insight_ru: string }[];
    };
    lost_reason_database?: {
      title_ru: string;
      hint_ru: string;
      reason_options: { code: string; label_ru: string }[];
      by_reason?: { code: string; label_ru: string; count: number }[];
    };
    success_patterns?: {
      title_ru: string;
      hint_ru: string;
      patterns: { pattern_ru: string; insight_ru: string; action_hint_ru: string }[];
    };
  };
  commercial_evidence?: CommercialEvidence;
  finance_guard?: {
    negative_streak?: number;
    last_net_eur?: number;
    revenue_confidence?: {
      confidence_pct: number;
      label_ru: string;
      note_ru: string;
    };
    forecast?: {
      spend_eur: number;
      expected_gross_revenue_eur?: number;
      expected_income_eur: number;
      net_profit_forecast_eur?: number;
      cost_per_verified_eur?: number | null;
      cost_per_euro_note_ru?: string | null;
      roi_pct: number | null;
      summary_ru: string;
      expected_note_ru: string;
      gross_vs_profit_note_ru?: string;
    };
  };
};

type CommercialEvidence = {
  title_ru: string;
  verdict_ru: string;
  verdict_code: string;
  toloka_model_note_ru: string;
  rows: { step: string; title_ru: string; status: string; detail: string }[];
  tick_economics?: { earned_eur: number; llm_cost_eur: number; net_eur: number; note_ru: string };
};

const ADAPTER_LABELS: Record<string, string> = {
  ai_labeling: "AI-разметка",
  data_clean: "Чистка данных",
  text_classify: "Классификация",
  record_verify: "Проверка",
  scale_ai_probe: "Scale (проверка)",
  toloka_probe: "Toloka (проверка)",
};

export function FarmDashboard() {
  const [dash, setDash] = useState<FarmDash | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [loadError, setLoadError] = useState("");
  const [quoteVolume, setQuoteVolume] = useState(18200);
  const [quoteService, setQuoteService] = useState("svc_data_qa");
  const [workers, setWorkers] = useState(10);
  const [quoteResult, setQuoteResult] = useState<{
    sell_price_eur?: number;
    internal_cost_eur?: number;
    margin_eur?: number;
    margin_pct?: number;
    duration_label_ru?: string;
    summary_ru?: string;
    invoice_line_ru?: string;
    truth_note_ru?: string;
  } | null>(null);
  const [proposalPreview, setProposalPreview] = useState<string>("");
  const [lostReasonCode, setLostReasonCode] = useState("expensive");
  const [lostTargetId, setLostTargetId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchApi(`${API}/api/farm/dashboard`, { timeoutMs: 20_000 });
      if (!res.ok) throw new Error("dashboard");
      setDash(await res.json());
      setLoadError("");
    } catch {
      setLoadError("Backend не отвечает. Genesis.exe → Запустить → «✔ Готов».");
    }
  }, []);

  useEffect(() => {
    refresh();
    const poll = window.setInterval(refresh, 15_000);
    return () => window.clearInterval(poll);
  }, [refresh]);

  useEffect(() => {
    if (!dash?.running) return;
    const tick = window.setInterval(async () => {
      try {
        await fetchApi(`${API}/api/farm/tick`, { method: "POST", timeoutMs: 8_000 });
        refresh();
      } catch {
        /* background */
      }
    }, 20_000);
    return () => window.clearInterval(tick);
  }, [dash?.running, refresh]);

  async function startFarm() {
    setBusy("start");
    setMessage("");
    try {
      const feed = await fetch(`${API}/api/farm/feed`, { method: "POST" });
      const feedBody = await feed.json().catch(() => ({}));
      const res = await fetch(`${API}/api/farm/start?workers=${workers}`, { method: "POST" });
      const body = await res.json();
      setMessage(feedBody.message ?? body.message ?? "Ферма запущена");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function stopFarm() {
    setBusy("stop");
    try {
      const res = await fetch(`${API}/api/farm/stop`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Остановлено");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function manualTick() {
    setBusy("tick");
    try {
      const res = await fetch(`${API}/api/farm/tick`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Готово");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function confirmEuroStep(stepId: string, done: boolean) {
    setBusy(`euro-${stepId}`);
    try {
      const res = await fetch(
        `${API}/api/farm/first-euro/confirm?step_id=${encodeURIComponent(stepId)}&done=${done}`,
        { method: "POST" },
      );
      const body = await res.json();
      setMessage(body.gate?.headline ?? "Отмечено");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function submitToloka() {
    setBusy("toloka");
    try {
      const res = await fetch(`${API}/api/farm/toloka/submit`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? (body.ok ? "Отправлено на Toloka" : "Ошибка Toloka"));
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runBattleTest() {
    setBusy("battle");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/farm/battle-test`, { method: "POST" });
      const body = await res.json();
      setMessage(body.verdict ?? body.message ?? "Тест завершён");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runLiveConnectTest() {
    setBusy("live");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/farm/test-connection-live`, { method: "POST" });
      const body = await res.json();
      setMessage(body.log_line ?? body.message ?? "Live test done");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function fetchAutoQuote() {
    setBusy("quote");
    try {
      const res = await fetch(
        `${API}/api/farm/quote?service_id=${encodeURIComponent(quoteService)}&volume=${quoteVolume}&workers=${workers}`,
      );
      if (res.ok) setQuoteResult(await res.json());
    } finally {
      setBusy("");
    }
  }

  async function prepareOpportunityProposal(opportunityId: string) {
    setBusy(`prep-${opportunityId}`);
    try {
      const res = await fetch(
        `${API}/api/farm/opportunity-discovery/${encodeURIComponent(opportunityId)}/prepare`,
        { method: "POST" },
      );
      const body = await res.json();
      if (body.proposal_ru) setProposalPreview(body.proposal_ru);
      setMessage(
        body.message_ru ??
          `Черновик готов · Win ${body.win_probability_pct ?? body.evaluation?.win_probability_pct ?? "?"}% · отправьте сами`,
      );
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function recordLostReason(opportunityId: string) {
    setBusy(`lost-${opportunityId}`);
    try {
      const res = await fetch(
        `${API}/api/farm/opportunity-discovery/${encodeURIComponent(opportunityId)}/lost?reason_code=${encodeURIComponent(lostReasonCode)}`,
        { method: "POST" },
      );
      const body = await res.json();
      setMessage(body.message_ru ?? "Причина отказа сохранена");
      setLostTargetId(null);
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runRevenueReplay() {
    setBusy("replay");
    try {
      const res = await fetch(`${API}/api/farm/revenue-replay`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Revenue Replay");
      refresh();
    } finally {
      setBusy("");
    }
  }

  const connectedPlatforms = dash?.platforms.filter((p) => p.connected).length ?? 0;
  const totalPlatforms = dash?.platforms.length ?? 0;

  return (
    <main className="min-h-screen pb-16">
      <div className="mx-auto max-w-4xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/50 via-genesis-panel to-genesis-panel p-6">
          <div
            className={`mb-4 rounded-xl border px-4 py-3 text-center ${
              dash?.farm_program?.verified_revenue_status === "VERIFIED"
                ? "border-emerald-400/60 bg-emerald-950/40"
                : "border-rose-500/50 bg-rose-950/30"
            }`}
          >
            <p className="text-[10px] uppercase tracking-[0.4em] text-white/60">Mission 1</p>
            <p
              className={`text-2xl font-black tracking-wide ${
                dash?.farm_program?.verified_revenue_status === "VERIFIED"
                  ? "text-emerald-300"
                  : "text-rose-300"
              }`}
            >
              Verified Revenue · {dash?.farm_program?.verified_revenue_status ?? "NOT VERIFIED"}
            </p>
            <p className="mt-1 text-[11px] text-white/70">
              VRE LEVEL {dash?.first_euro_gate?.vre_level ?? dash?.farm_program?.vre_level ?? 0} · до VERIFIED —
              только полевой эксперимент
            </p>
          </div>
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/90">
            Genesis Production Platform · B2B
          </p>
          <h1 className="mt-2 text-3xl font-bold text-white">
            Фабрика данных · {dash?.owner_name ?? "…"}
          </h1>
          <p className="mt-2 text-sm text-genesis-muted">
            {dash?.production_platform?.subtitle_ru ??
              "Конвейер: Spider → Workers → Export → B2B / адаптеры. Toloka — только crash-test."}
          </p>
          <p className="mt-1 text-xs text-sky-200/80">
            {dash?.production_platform?.conveyor_status_ru ?? ""}
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link href="/journal" className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-emerald-100 hover:bg-emerald-950/30">
              Журнал · live
            </Link>
            <Link href="/monitor" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Пульт CEO
            </Link>
            <Link href="/finance" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Деньги
            </Link>
            <a
              href={`${API}/api/farm/export/labels`}
              className="rounded-lg border border-violet-500/40 px-3 py-1.5 text-violet-200 hover:bg-violet-950/30"
            >
              Скачать разметку{dash?.labels_export_count ? ` (${dash.labels_export_count})` : ""}
            </a>
          </div>
        </header>

        {loadError ? (
          <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-sm text-rose-200 space-y-2">
            <p>{loadError}</p>
            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs text-rose-100 hover:bg-rose-950/40"
            >
              Повторить
            </button>
          </div>
        ) : null}

        {dash?.production_platform?.b2b_brief ? (
          <section className="genesis-card border-sky-500/30 bg-sky-950/10 p-5 space-y-4">
            <h2 className="text-lg font-bold text-sky-100">{dash.production_platform.b2b_brief.tagline_ru}</h2>
            <p className="text-sm text-white/90">{dash.production_platform.b2b_brief.pitch_ru}</p>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-950/15 p-3 text-xs">
                <p className="font-semibold text-emerald-200">Что продаём бизнесу</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-white/85">
                  {farmList(dash.production_platform.b2b_brief.we_sell_ru).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-lg border border-sky-500/20 bg-sky-950/15 p-3 text-xs">
                <p className="font-semibold text-sky-200">Какие проблемы решаем</p>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-white/85">
                  {farmList(dash.production_platform.b2b_brief.problems_we_solve_ru).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {farmList(dash.production_platform.b2b_brief.packages_ru).map((pkg) => (
                <div key={pkg.scenario} className="rounded-lg border border-white/10 p-3 text-xs">
                  <p className="font-semibold text-emerald-200">{pkg.scenario}</p>
                  <p className="mt-1 text-white/80">«{pkg.client_says}»</p>
                  <p className="mt-2 text-sky-100">{pkg.genesis_says}</p>
                </div>
              ))}
            </div>
            {dash.production_platform.product_catalog ? (
              <div>
                <h3 className="text-sm font-bold text-white">Product Catalog</h3>
                <table className="mt-2 w-full text-left text-xs">
                  <thead>
                    <tr className="text-genesis-muted">
                      <th className="pb-2 pr-2">#</th>
                      <th className="pb-2 pr-2">Услуга</th>
                      <th className="pb-2 pr-2">Цена B2B</th>
                      <th className="pb-2">SLA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {farmList(dash.production_platform.product_catalog).map((s) => (
                      <tr key={s.service_number} className="border-t border-white/5">
                        <td className="py-2 pr-2">{s.service_number}</td>
                        <td className="py-2 pr-2 text-white">{s.title_ru}</td>
                        <td className="py-2 pr-2 text-emerald-200">
                          {s.price_b2b_eur} {s.unit_label_ru}
                        </td>
                        <td className="py-2 text-genesis-muted">{s.sla_example_ru}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {dash.production_platform.capability_marketplace ? (
              <div className="flex flex-wrap gap-2">
                {farmList(dash.production_platform.capability_marketplace).map((c) => (
                  <span
                    key={c.id}
                    className={`rounded px-2 py-1 text-[10px] ${
                      c.ready ? "bg-emerald-900/50 text-emerald-200" : "bg-white/5 text-white/50"
                    }`}
                  >
                    {c.ready ? "✓" : "○"} {c.label_ru}
                  </span>
                ))}
              </div>
            ) : null}
            <div className="rounded-lg border border-violet-500/30 bg-violet-950/15 p-4">
              <h3 className="text-sm font-bold text-violet-100">Auto Quote · Cost Engine</h3>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <select
                  value={quoteService}
                  onChange={(e) => setQuoteService(e.target.value)}
                  className="rounded border border-white/20 bg-black/30 px-2 py-1 text-white"
                >
                  <option value="svc_data_qa">Проверка данных</option>
                  <option value="svc_document_labeling">Разметка документов</option>
                  <option value="svc_ocr">OCR</option>
                  <option value="svc_catalog">Каталог товаров</option>
                  <option value="svc_translation_qa">Translation QA</option>
                </select>
                <input
                  type="number"
                  value={quoteVolume}
                  onChange={(e) => setQuoteVolume(Number(e.target.value) || 0)}
                  className="w-32 rounded border border-white/20 bg-black/30 px-2 py-1 text-white"
                  min={1}
                />
                <button
                  type="button"
                  disabled={busy === "quote"}
                  onClick={() => void fetchAutoQuote()}
                  className="rounded border border-violet-400/50 px-3 py-1 text-violet-100 hover:bg-violet-950/40"
                >
                  {busy === "quote" ? "…" : "Рассчитать"}
                </button>
              </div>
              {quoteResult?.summary_ru ? (
                <p className="mt-3 text-sm text-emerald-100">{quoteResult.summary_ru}</p>
              ) : null}
              {quoteResult?.internal_cost_eur != null && quoteResult.sell_price_eur != null ? (
                <p className="mt-2 text-xs text-white/80">
                  Себестоимость {quoteResult.internal_cost_eur.toFixed(2)} € · продать{" "}
                  {quoteResult.sell_price_eur.toFixed(2)} €
                  {quoteResult.margin_pct != null ? ` · маржа ${quoteResult.margin_pct}%` : ""}
                </p>
              ) : null}
              {quoteResult?.invoice_line_ru ? (
                <p className="mt-1 text-xs text-white/80">{quoteResult.invoice_line_ru}</p>
              ) : null}
              {quoteResult?.truth_note_ru ? (
                <p className="mt-1 text-[10px] text-amber-200/80">{quoteResult.truth_note_ru}</p>
              ) : null}
            </div>
            {dash.production_platform.revenue_router ? (
              <div>
                <h3 className="text-sm font-bold text-amber-100">{dash.production_platform.revenue_router.recommended_ru}</h3>
                <ul className="mt-2 space-y-1 text-xs">
                  {farmList(dash.production_platform.revenue_router?.channels).map((ch) => (
                    <li key={ch.id} className="flex flex-wrap gap-2 text-white/85">
                      <span className="font-medium">{ch.label_ru}</span>
                      <span className="text-emerald-300">{ch.potential_ru}</span>
                      <span className="text-genesis-muted">{ch.why_ru}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <p className="text-[11px] text-genesis-muted">{dash.production_platform.b2b_brief.cta_ru}</p>
          </section>
        ) : null}

        {dash?.opportunity_discovery ? (
          <section className="genesis-card border-amber-500/35 bg-amber-950/10 p-5 space-y-4">
            <div>
              <p className="text-[10px] uppercase tracking-[0.35em] text-amber-300/80">Opportunity Discovery</p>
              <h2 className="text-lg font-bold text-amber-100">{dash.opportunity_discovery.title_ru}</h2>
              <p className="text-sm text-white/85">{dash.opportunity_discovery.subtitle_ru}</p>
              {dash.opportunity_discovery.stats ? (
                <p className="mt-2 text-xs text-amber-200/90">
                  Найдено и оценено: <strong>{dash.opportunity_discovery.stats.evaluated}</strong> · Win ≥55%:{" "}
                  <strong>{dash.opportunity_discovery.stats.high_win_probability}</strong> · Потенциал топ-5:{" "}
                  <strong>{formatEur(dash.opportunity_discovery.stats.pipeline_value_eur)}</strong>
                </p>
              ) : null}
            </div>

            {dash.opportunity_discovery.ceo_hints_ru ? (
              <div className="rounded-lg border border-sky-500/25 bg-sky-950/15 p-3 text-xs text-sky-100">
                <p className="font-semibold">Как работать с этим блоком</p>
                <ul className="mt-2 list-decimal space-y-1 pl-4 text-white/85">
                  {farmList(dash.opportunity_discovery.ceo_hints_ru).map((h) => (
                    <li key={h}>{h}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dash.opportunity_discovery.confidence ? (
              <div className="rounded-lg border border-violet-500/30 bg-violet-950/15 p-3 text-xs">
                <p className="font-semibold text-violet-100">
                  Уверенность в оценке: {dash.opportunity_discovery.confidence.confidence_pct}%
                </p>
                <p className="mt-1 text-white/80">{dash.opportunity_discovery.confidence.honesty_note_ru}</p>
                {dash.opportunity_discovery.confidence.ceo_goal_ru ? (
                  <p className="mt-2 font-medium text-emerald-200">
                    {dash.opportunity_discovery.confidence.ceo_goal_ru}
                  </p>
                ) : null}
                <ul className="mt-2 list-disc space-y-0.5 pl-4 text-white/75">
                  {farmList(dash.opportunity_discovery.confidence.confidence_reasons_ru).map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dash.opportunity_discovery.learning_timeline ? (
              <div className="rounded-lg border border-sky-500/25 bg-sky-950/15 p-3 text-xs">
                <p className="font-semibold text-sky-100">{dash.opportunity_discovery.learning_timeline.title_ru}</p>
                <p className="mt-1 text-genesis-muted">{dash.opportunity_discovery.learning_timeline.hint_ru}</p>
                <ul className="mt-2 space-y-2">
                  {farmList(dash.opportunity_discovery.learning_timeline.stages).map((s) => (
                    <li key={s.milestone} className="flex flex-wrap gap-2 text-white/85">
                      <span
                        className={
                          s.status === "done"
                            ? "text-emerald-300"
                            : s.status === "current"
                              ? "text-amber-200"
                              : "text-white/50"
                        }
                      >
                        {s.status === "done" ? "✓" : s.status === "current" ? "→" : "○"}
                      </span>
                      <strong>{s.title_ru}</strong>
                      <span className="text-genesis-muted">{s.insight_ru}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dash.opportunity_discovery.success_patterns ? (
              <div className="rounded-lg border border-emerald-500/25 bg-emerald-950/15 p-3 text-xs">
                <p className="font-semibold text-emerald-200">{dash.opportunity_discovery.success_patterns.title_ru}</p>
                <p className="mt-1 text-genesis-muted">{dash.opportunity_discovery.success_patterns.hint_ru}</p>
                <ul className="mt-2 space-y-2">
                  {farmList(dash.opportunity_discovery.success_patterns.patterns).map((p) => (
                    <li key={p.pattern_ru} className="text-white/85">
                      <strong>{p.pattern_ru}</strong> — {p.insight_ru}
                      <span className="block text-emerald-200/80">→ {p.action_hint_ru}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dash.opportunity_discovery.top_opportunities && dash.opportunity_discovery.top_opportunities.length > 0 ? (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white">Активные возможности · не деньги, а шансы</h3>
                {farmList(dash.opportunity_discovery.top_opportunities).slice(0, 6).map((opp) => (
                  <div
                    key={opp.opportunity_id}
                    className="rounded-lg border border-amber-500/20 bg-black/25 p-3 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold text-white">{opp.company_name}</p>
                      <div className="flex flex-wrap gap-1">
                        <span className="rounded-full bg-amber-900/50 px-2 py-0.5 text-amber-100">
                          Score {opp.opportunity_score_pct ?? "—"}
                        </span>
                        <span className="rounded-full bg-violet-900/60 px-2 py-0.5 font-bold text-violet-100">
                          Win {opp.win_probability_pct}%
                        </span>
                        <span className="rounded-full bg-sky-900/50 px-2 py-0.5 text-sky-100">
                          Conf {opp.confidence_pct ?? "?"}%
                        </span>
                      </div>
                    </div>
                    <p className="mt-1 text-white/80">
                      Проблема: {opp.primary_problem_ru ?? opp.service_label_ru} · Стоимость:{" "}
                      <strong className="text-emerald-200">{formatEur(opp.sell_price_eur)}</strong>
                      {opp.duration_label_ru ? ` · Срок: ${opp.duration_label_ru}` : ""}
                    </p>
                    {opp.confidence_reasons_ru?.length ? (
                      <p className="mt-1 text-[10px] text-sky-200/70">
                        Confidence {opp.confidence_pct}%: {opp.confidence_reasons_ru[0]}
                      </p>
                    ) : null}
                    {opp.lifetime_value?.repeat_sale_probability_pct ? (
                      <p className="mt-1 text-emerald-200/90">
                        Повторная продажа: {opp.lifetime_value.repeat_sale_probability_pct}% ·{" "}
                        {opp.lifetime_value.contact_reminder_ru}
                      </p>
                    ) : null}
                    {opp.win_probability_reasons_ru?.length ? (
                      <div className="mt-2 rounded border border-white/5 bg-black/30 p-2">
                        <p className="font-medium text-amber-200">Почему именно {opp.win_probability_pct}%</p>
                        <ul className="mt-1 list-disc space-y-0.5 pl-4 text-white/75">
                          {farmList(opp.win_probability_reasons_ru).map((r) => (
                            <li key={r}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {opp.market_memory?.prior_lost ? (
                      <p className="mt-1 text-rose-200/80">
                        Память: был отказ ({opp.market_memory.prior_lost}×)
                        {opp.market_memory.last_lost_reason_ru ? ` — ${opp.market_memory.last_lost_reason_ru}` : ""}
                      </p>
                    ) : null}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {opp.proposal_ready ? (
                        <button
                          type="button"
                          disabled={busy === `prep-${opp.opportunity_id}`}
                          onClick={() => void prepareOpportunityProposal(opp.opportunity_id)}
                          className="rounded border border-emerald-500/40 px-3 py-1 text-emerald-100 hover:bg-emerald-950/30"
                        >
                          {busy === `prep-${opp.opportunity_id}` ? "…" : "Подготовить предложение"}
                        </button>
                      ) : null}
                      <button
                        type="button"
                        onClick={() =>
                          setLostTargetId(lostTargetId === opp.opportunity_id ? null : opp.opportunity_id)
                        }
                        className="rounded border border-rose-500/30 px-3 py-1 text-rose-200 hover:bg-rose-950/30"
                      >
                        Клиент отказал
                      </button>
                    </div>
                    {lostTargetId === opp.opportunity_id ? (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <select
                          value={lostReasonCode}
                          onChange={(e) => setLostReasonCode(e.target.value)}
                          className="rounded border border-white/20 bg-black/40 px-2 py-1 text-white"
                        >
                          {(dash?.opportunity_discovery?.lost_reason_database?.reason_options ?? []).map((o) => (
                            <option key={o.code} value={o.code}>
                              {o.label_ru}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          disabled={busy === `lost-${opp.opportunity_id}`}
                          onClick={() => void recordLostReason(opp.opportunity_id)}
                          className="rounded border border-rose-400/40 px-2 py-1 text-rose-100"
                        >
                          Запомнить причину
                        </button>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-genesis-muted">
                Пока пусто. Нажмите «Запустить ферму» — Spider найдёт компании. Здесь появятся проблемы, цена и Win
                Probability.
              </p>
            )}

            {proposalPreview ? (
              <pre className="max-h-48 overflow-auto rounded border border-white/10 bg-black/40 p-3 text-[11px] text-white/90 whitespace-pre-wrap">
                {proposalPreview}
              </pre>
            ) : null}

            {dash.opportunity_discovery.lost_reason_database ? (
              <div className="rounded-lg border border-rose-500/20 bg-rose-950/10 p-3 text-xs">
                <p className="font-semibold text-rose-100">{dash.opportunity_discovery.lost_reason_database.title_ru}</p>
                <p className="mt-1 text-genesis-muted">{dash.opportunity_discovery.lost_reason_database.hint_ru}</p>
                {dash.opportunity_discovery.lost_reason_database.by_reason?.length ? (
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {farmList(dash.opportunity_discovery.lost_reason_database?.by_reason).map((r) => (
                      <li key={r.code} className="rounded bg-black/30 px-2 py-1 text-white/80">
                        {r.label_ru}: {r.count}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-white/60">Пока нет отказов — база наполнится после первых «Клиент отказал».</p>
                )}
              </div>
            ) : null}

            {dash.opportunity_discovery.cto_warning_ru ? (
              <p className="rounded border border-rose-500/30 bg-rose-950/20 p-2 text-[11px] text-rose-100">
                {dash.opportunity_discovery.cto_warning_ru}
              </p>
            ) : null}

            {dash.opportunity_discovery.automation_level_ru ? (
              <p className="text-[10px] text-genesis-muted">{dash.opportunity_discovery.automation_level_ru}</p>
            ) : null}
          </section>
        ) : null}

        {dash?.first_euro_gate ? (
          <section
            className={`genesis-card p-5 ${
              dash.first_euro_gate.verdict === "PASS"
                ? "border-emerald-500/40 bg-emerald-950/15"
                : dash.first_euro_gate.verdict === "CHANNEL_REVIEW"
                  ? "border-rose-500/50 bg-rose-950/20"
                : dash.first_euro_gate.verdict === "COMMERCIAL_GATE"
                  ? "border-amber-500/40 bg-amber-950/15"
                  : "border-sky-500/30 bg-sky-950/10"
            }`}
          >
            <h2 className="text-sm font-bold text-white">
              {dash.first_euro_gate.title_ru ?? "Движок проверяемого дохода (VRE)"}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-sky-400/50 bg-sky-950/40 px-3 py-1 text-xs font-semibold text-sky-100">
                VRE LEVEL {dash.first_euro_gate.vre_level ?? dash.first_euro_gate.vre?.level ?? 0}
              </span>
              {dash.first_euro_gate.vre?.level_label_ru ? (
                <span className="text-[11px] text-white/75">{dash.first_euro_gate.vre.level_label_ru}</span>
              ) : null}
            </div>
            {dash.first_euro_gate.mission1_freeze ? (
              <div className="mt-3 rounded-lg border border-white/10 bg-black/20 p-3 text-[11px] text-white/85">
                <p className="font-semibold">{dash.first_euro_gate.mission1_freeze.title_ru}</p>
                {dash.first_euro_gate.mission1_freeze.pr_gate_question_ru ? (
                  <p className="mt-2 rounded border border-amber-500/30 bg-amber-950/20 p-2 text-amber-100">
                    PR: {dash.first_euro_gate.mission1_freeze.pr_gate_question_ru}{" "}
                    {dash.first_euro_gate.mission1_freeze.pr_gate_rule_ru ?? "→ Нет = не принимается"}
                  </p>
                ) : null}
                <p className="mt-1 text-emerald-200/90">
                  ✓ {dash.first_euro_gate.mission1_freeze.allowed_ru.join(" · ")}
                </p>
                <p className="mt-1 text-rose-200/80">
                  ✗ {dash.first_euro_gate.mission1_freeze.forbidden_ru.join(" · ")}
                </p>
                {dash.first_euro_gate.mission1_freeze.until_ru ? (
                  <p className="mt-1 text-genesis-muted">{dash.first_euro_gate.mission1_freeze.until_ru}</p>
                ) : null}
              </div>
            ) : null}
            {dash.first_euro_gate.channel_review_message_ru ? (
              <p className="mt-3 rounded border border-rose-500/40 bg-rose-950/30 p-2 text-xs text-rose-100">
                {dash.first_euro_gate.channel_review_message_ru}
              </p>
            ) : null}
            <p className="mt-1 text-xs text-white/80">{dash.first_euro_gate.core_question}</p>
            <p className="mt-2 text-sm font-medium text-emerald-100">{dash.first_euro_gate.headline}</p>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Авто: {dash.first_euro_gate.auto_steps_done}/{dash.first_euro_gate.auto_steps_total} ·{" "}
              {dash.first_euro_gate.ceo_action_now}
            </p>
            <ol className="mt-4 space-y-2">
              {farmList(dash.first_euro_gate.steps).map((step) => (
                <li
                  key={step.id}
                  className="flex flex-wrap items-start justify-between gap-2 rounded-lg border border-white/5 px-3 py-2 text-xs"
                >
                  <div>
                    <p className={step.done ? "text-emerald-300" : "text-white/90"}>
                      {step.done ? "✓" : "○"} {step.title}
                      {step.kind === "manual" ? " (CEO)" : ""}
                    </p>
                    <p className="mt-0.5 text-genesis-muted">{step.detail}</p>
                  </div>
                  {step.kind === "manual" && !step.done ? (
                    <button
                      type="button"
                      disabled={busy === `euro-${step.id}`}
                      onClick={() => void confirmEuroStep(step.id, true)}
                      className="shrink-0 rounded border border-emerald-500/40 px-2 py-1 text-[10px] text-emerald-200 hover:bg-emerald-950/30"
                    >
                      Подтверждаю
                    </button>
                  ) : null}
                </li>
              ))}
            </ol>
          </section>
        ) : null}

        {dash?.farm_program ? (
          <section className="genesis-card border-emerald-500/20 p-5 space-y-5">
            <div>
              <h2 className="text-sm font-bold text-emerald-100">{dash.farm_program.title_ru}</h2>
              <p className="mt-1 text-[11px] text-genesis-muted">{dash.farm_program.pipeline?.diagram_ru}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {farmList(dash.farm_program.pipeline?.stages).map((s) => (
                  <span
                    key={s.id}
                    className={`rounded px-2 py-1 text-[10px] ${
                      s.done ? "bg-emerald-900/50 text-emerald-200" : "bg-white/5 text-white/50"
                    }`}
                  >
                    {s.done ? "✓" : "○"} {s.title}
                  </span>
                ))}
              </div>
            </div>

            {dash.farm_program.revenue_path_map ? (
              <div className="rounded-lg border border-amber-500/25 bg-amber-950/10 p-4">
                <h3 className="text-xs font-bold text-amber-100">{dash.farm_program.revenue_path_map.title_ru}</h3>
                <p className="mt-1 text-sm text-white">
                  Сейчас: <strong>{dash.farm_program.revenue_path_map.current_step_ru}</strong>
                </p>
                <p className="text-[11px] text-amber-200/90">{dash.farm_program.revenue_path_map.current_money_note_ru}</p>
                {dash.farm_program.revenue_path_map.blocker_ru ? (
                  <p className="mt-2 text-xs text-rose-200">{dash.farm_program.revenue_path_map.blocker_ru}</p>
                ) : null}
                <ol className="mt-3 space-y-1.5">
                  {farmList(dash.farm_program.revenue_path_map.steps).map((step) => (
                    <li key={step.id} className="flex flex-wrap gap-2 text-[11px]">
                      <span className={step.done ? "text-emerald-300" : "text-white/60"}>
                        {step.done ? "✓" : "○"} {step.title_ru}
                      </span>
                      <span className="rounded bg-white/5 px-1.5 text-[10px] text-sky-200">{step.truth_kind}</span>
                      <span className="text-genesis-muted">{step.money_ru}</span>
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}

            {dash.farm_program.explainability ? (
              <div className="rounded-lg border border-sky-500/25 bg-sky-950/10 p-4">
                <h3 className="text-xs font-bold text-sky-100">{dash.farm_program.explainability.title_ru}</h3>
                <p className="mt-1 text-sm text-white">{dash.farm_program.explainability.recommendation_ru}</p>
                <ul className="mt-2 list-inside list-disc text-[11px] text-white/80">
                  {farmList(dash.farm_program.explainability.reasons).filter(Boolean).map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
                {dash.farm_program.explainability.probabilities &&
                Object.keys(dash.farm_program.explainability.probabilities).length > 0 ? (
                  <p className="mt-2 text-[11px] text-violet-200">
                    {Object.entries(dash.farm_program.explainability.probabilities).map(([k, v]) => (
                      <span key={k} className="mr-3">
                        {k}: {v}
                      </span>
                    ))}
                  </p>
                ) : null}
              </div>
            ) : null}

            {dash.farm_program.truth_engine ? (
              <div className="rounded-lg border border-white/10 p-4">
                <h3 className="text-xs font-bold text-white">{dash.farm_program.truth_engine.title_ru}</h3>
                <table className="mt-2 w-full text-left text-[11px]">
                  <tbody>
                    {farmList(dash.farm_program.truth_engine.records).map((rec) => (
                      <tr key={rec.label_ru} className="border-t border-white/5">
                        <td className="py-1.5 pr-2 text-white/90">{rec.label_ru}</td>
                        <td className="py-1.5 pr-2 font-mono text-emerald-200">{String(rec.value)}</td>
                        <td className="py-1.5">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] ${
                              rec.truth_kind === "FACT"
                                ? "bg-emerald-900/60 text-emerald-200"
                                : rec.truth_kind === "CEO_CONFIRMATION"
                                  ? "bg-violet-900/60 text-violet-200"
                                  : rec.truth_kind === "ESTIMATE"
                                    ? "bg-amber-900/60 text-amber-200"
                                    : "bg-white/10 text-white/70"
                            }`}
                          >
                            {rec.truth_kind}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {dash.farm_program.error_ledger && dash.farm_program.error_ledger.total_logged > 0 ? (
              <div className="rounded-lg border border-rose-500/30 bg-rose-950/15 p-4">
                <h3 className="text-xs font-bold text-rose-100">Error Ledger v0</h3>
                <p className="mt-1 text-sm text-white">Reject залогировано: {dash.farm_program.error_ledger.total_logged}</p>
                {dash.farm_program.error_ledger.hint_ru ? (
                  <p className="mt-1 text-xs text-rose-200">{dash.farm_program.error_ledger.hint_ru}</p>
                ) : null}
                {dash.farm_program.error_ledger.last_entry ? (
                  <p className="mt-2 text-[11px] text-genesis-muted">
                    Последнее: {dash.farm_program.error_ledger.last_entry.taxonomy_ru} —{" "}
                    {dash.farm_program.error_ledger.last_entry.message?.slice(0, 120)}
                  </p>
                ) : null}
              </div>
            ) : null}

            {dash.farm_program.force_vectors ? (
              <div className="rounded-lg border border-violet-500/20 p-4">
                <h3 className="text-xs font-bold text-violet-100">{dash.farm_program.force_vectors.title_ru}</h3>
                <p className="mt-1 text-[10px] text-genesis-muted">{dash.farm_program.force_vectors.note_ru}</p>
                <ul className="mt-3 space-y-2">
                  {farmList(dash.farm_program.force_vectors.vectors).map((v) => (
                    <li
                      key={v.id}
                      className={`rounded border px-3 py-2 text-[11px] ${
                        v.unlocked ? "border-emerald-500/30 bg-emerald-950/10" : "border-white/5 bg-black/20 opacity-80"
                      }`}
                    >
                      <p className="font-semibold text-white">
                        {v.unlocked ? "●" : "○"} {v.title_ru}
                      </p>
                      <p className="text-genesis-muted">{v.subtitle_ru}</p>
                      <p className="mt-0.5 text-violet-200/90">{v.status_ru}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {dash.farm_program.post_first_revenue_questions_ru ? (
              <ul className="list-inside list-disc text-[11px] text-white/70">
                {farmList(dash.farm_program.post_first_revenue_questions_ru).map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {dash?.finance_guard?.forecast ? (
          <section className="genesis-card border-violet-500/25 p-5">
            <h2 className="text-sm font-bold text-violet-100">Finance Guard · прогноз</h2>
            <p className="mt-2 text-lg text-white">{dash.finance_guard.forecast.summary_ru}</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
              <div className="rounded-lg border border-white/10 p-3">
                <p className="text-[11px] text-genesis-muted">Расход сегодня</p>
                <p className="font-bold text-rose-200">{dash.finance_guard.forecast.spend_eur.toFixed(2)} €</p>
              </div>
              <div className="rounded-lg border border-white/10 p-3">
                <p className="text-[11px] text-genesis-muted">Expected Gross Revenue</p>
                <p className="font-bold text-emerald-200">
                  {(
                    dash.finance_guard.forecast.expected_gross_revenue_eur ??
                    dash.finance_guard.forecast.expected_income_eur
                  ).toFixed(2)}{" "}
                  €
                </p>
              </div>
              <div className="rounded-lg border border-white/10 p-3">
                <p className="text-[11px] text-genesis-muted">Прибыль (net)</p>
                <p className="font-bold text-emerald-100">
                  {(dash.finance_guard.forecast.net_profit_forecast_eur ?? 0).toFixed(2)} €
                </p>
              </div>
              <div className="rounded-lg border border-white/10 p-3">
                <p className="text-[11px] text-genesis-muted">ROI</p>
                <p className="font-bold text-violet-200">
                  {dash.finance_guard.forecast.roi_pct != null
                    ? `${dash.finance_guard.forecast.roi_pct}%`
                    : "—"}
                </p>
              </div>
            </div>
            {(dash.finance_guard.revenue_confidence ??
              dash.first_euro_gate?.revenue_confidence) ? (
              <div className="mt-3 rounded-lg border border-violet-500/30 bg-violet-950/20 p-3">
                <p className="text-[11px] text-genesis-muted">Revenue Confidence</p>
                <p className="text-xl font-bold text-violet-100">
                  {(
                    dash.finance_guard.revenue_confidence ??
                    dash.first_euro_gate!.revenue_confidence!
                  ).confidence_pct}
                  %
                </p>
                <p className="text-xs text-white/80">
                  {(
                    dash.finance_guard.revenue_confidence ??
                    dash.first_euro_gate!.revenue_confidence!
                  ).label_ru}
                </p>
              </div>
            ) : null}
            <p className="mt-2 text-[11px] text-genesis-muted">
              {dash.finance_guard.forecast.gross_vs_profit_note_ru ??
                "Gross = оборот · Net = прибыль после LLM/VPS"}
            </p>
            <p className="mt-1 text-[11px] text-genesis-muted">{dash.finance_guard.forecast.expected_note_ru}</p>
            {dash.finance_guard.forecast.cost_per_euro_note_ru ? (
              <p className="mt-2 rounded border border-emerald-500/30 bg-emerald-950/20 p-2 text-xs text-emerald-100">
                {dash.finance_guard.forecast.cost_per_euro_note_ru}
              </p>
            ) : (
              <p className="mt-2 text-[11px] text-genesis-muted">
                Стоимость 1 € появится после CEO_CONFIRMATION wallet (подтверждённый доход)
              </p>
            )}
          </section>
        ) : null}

        {dash?.farm_program?.commercial_experiments && dash.farm_program.commercial_experiments.length > 0 ? (
          <section className="genesis-card border-white/10 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-bold text-white">Журнал коммерческих экспериментов</h2>
              <button
                type="button"
                disabled={busy === "replay"}
                onClick={() => void runRevenueReplay()}
                className="rounded-lg border border-violet-500/40 px-3 py-1.5 text-[11px] text-violet-200 hover:bg-violet-950/30"
              >
                {busy === "replay" ? "…" : "Revenue Replay"}
              </button>
            </div>
            <table className="mt-3 w-full text-left text-xs">
              <thead>
                <tr className="text-genesis-muted">
                  <th className="pb-2 pr-2">Дата</th>
                  <th className="pb-2 pr-2">Канал</th>
                  <th className="pb-2">Итог</th>
                </tr>
              </thead>
              <tbody>
                {farmList(dash.farm_program.commercial_experiments).map((row, i) => (
                  <tr key={`${row.channel}-${i}`} className="border-t border-white/5">
                    <td className="py-2 pr-2 text-white/70">{row.date_ru ?? "—"}</td>
                    <td className="py-2 pr-2 text-white/90">{row.channel}</td>
                    <td className="py-2 text-emerald-200/90">{row.outcome_ru}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}

        {(dash?.commercial_evidence ?? dash?.first_euro_gate?.commercial_evidence) ? (
          <section className="genesis-card border-white/10 p-5">
            <h2 className="text-sm font-bold text-white">
              {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)?.title_ru}
            </h2>
            <p className="mt-2 text-sm text-amber-100/90">
              {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)?.verdict_ru}
            </p>
            <p className="mt-2 text-[11px] text-genesis-muted">
              {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)?.toloka_model_note_ru}
            </p>
            <table className="mt-4 w-full text-left text-xs">
              <thead>
                <tr className="text-genesis-muted">
                  <th className="pb-2 pr-2">Шаг</th>
                  <th className="pb-2 pr-2">Статус</th>
                  <th className="pb-2">Детали</th>
                </tr>
              </thead>
              <tbody>
                {farmList(
                  (dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)?.rows
                ).map((row) => (
                  <tr key={row.step} className="border-t border-white/5">
                    <td className="py-2 pr-2 text-white/90">{row.title_ru}</td>
                    <td className="py-2 pr-2">{row.status}</td>
                    <td className="py-2 text-genesis-muted">{row.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)?.tick_economics ? (
              <p className="mt-3 text-[11px] text-violet-200/90">
                Tick: earned{" "}
                {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)!.tick_economics!.earned_eur.toFixed(4)}{" "}
                € · LLM{" "}
                {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)!.tick_economics!.llm_cost_eur.toFixed(4)}{" "}
                € · net{" "}
                {(dash.commercial_evidence ?? dash.first_euro_gate?.commercial_evidence)!.tick_economics!.net_eur.toFixed(4)} €
              </p>
            ) : null}
          </section>
        ) : null}

        {dash?.ceo_checklist && (
          <section className="genesis-card border-amber-500/30 bg-amber-950/15 p-5">
            <h2 className="text-sm font-bold text-amber-100">Что сделать тебе (по порядку)</h2>
            <ol className="mt-3 space-y-3">
              {farmList(dash.ceo_checklist).map((item) => (
                <li key={item.step} className="flex gap-3 text-sm">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-500/25 text-xs font-bold text-amber-100">
                    {item.step}
                  </span>
                  <div>
                    <p className="font-medium text-white">{item.title}</p>
                    <p className="text-xs text-amber-100/70">{item.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
            <p className="mt-3 text-[11px] text-amber-200/60">
              Шаблон ключей: dashboard/backend/env.platforms.example → скопируй строки в .env.local
            </p>
            {dash.prepare_live ? (
              <div className="mt-4 rounded-lg border border-emerald-500/25 bg-emerald-950/20 p-3">
                <p className="text-xs font-semibold text-emerald-100">
                  Боевой режим: {dash.prepare_live.farm_mode === "live" ? "LIVE" : "dry_run"}
                </p>
                <ul className="mt-2 space-y-1 text-xs text-emerald-200/80">
                  {farmList(dash.prepare_live.checklist).map((c) => (
                    <li key={c.step}>
                      {c.done ? "✓" : "○"} {c.title}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        )}

        {dash?.global_spider ? (
          <section className="genesis-card border-cyan-500/25 bg-cyan-950/10 p-5">
            <h2 className="text-sm font-bold text-cyan-100">Global Spider · вектор охоты</h2>
            <p className="mt-1 text-xs text-cyan-200/70">{dash.global_spider.note}</p>
            <p className="mt-2 text-sm text-white">
              Toloka-категорий: <strong>{dash.global_spider.toloka_categories_count}</strong> · Seeds:{" "}
              <strong>{dash.global_spider.seed_targets_count ?? 0}</strong> · Places:{" "}
              <strong>{dash.global_spider.places_queries_count}</strong>
              {dash.global_spider.places_configured ? " · Google Places 🟢" : " · Places ⚪ (нужен ключ)"}
            </p>
            <p className="mt-2 text-xs text-cyan-100/90">
              Фильтр ≥ <strong>{dash.global_spider.min_task_price?.toFixed(2) ?? "0.02"} €</strong> · Охота каждые{" "}
              <strong>{dash.global_spider.polling_interval_sec ?? 8} сек</strong>
              {dash.global_spider.hunter_mode ? " · режим охотника ON" : ""}
            </p>
            {dash.global_spider.toloka_task_categories?.length ? (
              <ul className="mt-3 flex flex-wrap gap-2 text-[11px]">
                {farmList(dash.global_spider.toloka_task_categories).slice(0, 8).map((t) => (
                  <li key={t} className="rounded-full border border-cyan-500/30 px-2 py-0.5 text-cyan-100/90">
                    {t}
                  </li>
                ))}
              </ul>
            ) : null}
            <p className="mt-3 text-xs text-genesis-muted">
              «Запустить ферму» = feed + Global Spider ищет сайты по places_queries.
            </p>
          </section>
        ) : null}

        {dash?.toloka_submit?.configured ? (
          <section className="genesis-card border-violet-500/30 bg-violet-950/10 p-5">
            <h2 className="text-sm font-bold text-violet-100">Toloka · crash-test (адаптер)</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              {dash?.production_platform?.toloka_role_ru ?? "Не центр стратегии — только проверка прочности"}
            </p>
            <p className="mt-1 text-xs text-violet-200/80">
              {dash.toloka_submit.auto_submit_enabled
                ? "Live: после каждого tick разметка уходит на platform.toloka.ai автоматически."
                : "Auto-submit выключен — нажми кнопку или включи TOLOKA_AUTO_SUBMIT=1."}
            </p>
            <p className="mt-2 text-sm text-white">
              Ожидает: <strong>{dash.toloka_submit.pending_count ?? 0}</strong> · Отправлено:{" "}
              <strong>{dash.toloka_submit.submitted_count ?? 0}</strong>
              {dash.toloka_submit.connected ? " · 🟢 API" : " · ⚪ offline"}
            </p>
            {dash.toloka_submit.last_error ? (
              <p className="mt-2 text-xs text-rose-300">{dash.toloka_submit.last_error}</p>
            ) : null}
            {dash.toloka_submit.circuit_breaker?.safe_mode ? (
              <p className="mt-2 rounded border border-amber-500/40 bg-amber-950/30 p-2 text-xs text-amber-100">
                Safe Mode · {dash.toloka_submit.circuit_breaker.safe_mode_reason ?? "circuit open"} ·{" "}
                {dash.toloka_submit.circuit_breaker.seconds_remaining}s
              </p>
            ) : null}
            {dash.toloka_submit.last_run_status ? (
              <p className="mt-2 text-xs text-violet-200/90">
                Pipeline run: {dash.toloka_submit.last_run_status}
              </p>
            ) : null}
            <button
              type="button"
              disabled={busy === "toloka" || !dash.toloka_submit.pending_count}
              onClick={() => void submitToloka()}
              className="mt-3 rounded-xl border border-violet-400/40 px-4 py-2 text-sm text-violet-100 hover:bg-violet-950/40 disabled:opacity-40"
            >
              {busy === "toloka" ? "Отправка…" : "Отправить на Toloka сейчас"}
            </button>
          </section>
        ) : null}

        {dash?.scale_ai ? (
          <p
            className={`rounded-xl border px-4 py-2 text-xs ${
              dash.scale_ai.connected
                ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-200"
                : "border-amber-500/30 bg-amber-950/20 text-amber-100"
            }`}
          >
            {dash.scale_ai.log_line ?? `Scale AI: ${dash.scale_ai.status_label}`}
            {dash.scale_ai.message ? ` — ${dash.scale_ai.message}` : ""}
          </p>
        ) : null}

        {dash?.priority_manager ? (
          <section className="genesis-card border-violet-500/25 bg-violet-950/10 p-5">
            <h2 className="text-sm font-bold text-violet-100">Менеджер приоритетов</h2>
            <p className="mt-1 text-xs text-violet-200/70">{dash.priority_manager.async_note}</p>
            <p className="mt-1 text-xs text-violet-200/70">{dash.priority_manager.router_note}</p>
            <p className="mt-3 text-sm text-white">
              {dash.priority_manager.learning.note}
              {dash.priority_manager.learning.investor_mode && dash.priority_manager.learning.top_adapter
                ? ` · Лидер: ${ADAPTER_LABELS[dash.priority_manager.learning.top_adapter] ?? dash.priority_manager.learning.top_adapter}`
                : ""}
            </p>
            <p className="mt-2 text-xs text-genesis-muted">
              Кэш паттернов: {dash.priority_manager.cache.entries} / {dash.priority_manager.cache.max_entries}
            </p>
            {dash.priority_manager.cloud_dispatcher ? (
              <p className="mt-2 text-xs text-violet-200/80">
                Облако: режим <strong>{dash.priority_manager.cloud_dispatcher.execution_mode}</strong>
                {dash.priority_manager.cloud_dispatcher.pool_configured
                  ? ` · пул ${dash.priority_manager.cloud_dispatcher.pool.ok ? "онлайн" : "offline"}`
                  : " · пульт на ноутбуке (задай FARM_WORKER_POOL_URL для VPS)"}
              </p>
            ) : null}
          </section>
        ) : null}

        {dash?.dry_run?.active ? (
          <section className="genesis-card border-sky-500/30 bg-sky-950/15 p-5">
            <h2 className="text-sm font-bold text-sky-100">DRY RUN · local</h2>
            <p className="mt-1 text-xs text-sky-200/80">{dash.dry_run.note}</p>
            <p className="mt-2 text-sm text-white">
              Консоль: <code className="text-sky-200">{dash.dry_run.log_format}</code>
            </p>
            <p className="mt-2 text-sm text-emerald-200">
              Серия: <strong>{dash.dry_run.streak}</strong> / {dash.dry_run.milestone_target}
              {dash.dry_run.milestone_reached ? " · ✓ билет на VPS подтверждён математикой" : ""}
            </p>
            <p className="mt-1 text-xs text-genesis-muted">
              Суммарный потенциал (прогноз): {formatEur(dash.dry_run.total_potential_eur)}
            </p>
            {dash.dry_run.task_selection?.pipeline ? (
              <ol className="mt-3 space-y-1 text-xs text-sky-100/80">
                {farmList(dash.dry_run.task_selection?.pipeline).map((p) => (
                  <li key={p.step}>
                    {p.step}. <strong>{p.name}</strong> — {p.detail}
                  </li>
                ))}
              </ol>
            ) : null}
          </section>
        ) : null}

        {dash?.payment_monitor?.monitor ? (
          <section className="genesis-card border-emerald-500/30 bg-emerald-950/15 p-5">
            <h2 className="text-sm font-bold text-emerald-100">
              Биржа · реальное время{dash?.dry_run?.active ? " (ключ проверен)" : " · LIVE"}
            </h2>
            <p className="mt-1 text-xs text-emerald-200/70">
              FARM_LIVE_MODE={dash.payment_monitor.monitor.farm_mode}
              {dash.payment_monitor.monitor.execution_mode
                ? ` · FARM_EXECUTION_MODE=${dash.payment_monitor.monitor.execution_mode}`
                : ""}
            </p>
            {dash.payment_monitor.note ? (
              <p className="mt-1 text-xs text-emerald-200/70">{dash.payment_monitor.note}</p>
            ) : null}
            {dash.payment_monitor.remote_warning ? (
              <p className="mt-2 rounded-lg border border-amber-500/30 bg-amber-950/20 p-2 text-xs text-amber-100">
                {dash.payment_monitor.remote_warning}
              </p>
            ) : null}
            <p className="mt-1 text-xs text-emerald-200/70">
              Порог вывода: ${dash.payment_monitor.payout?.threshold_usd ?? 10} · Stripe вручную с биржи
            </p>
            <div className="mt-3 space-y-2 text-xs text-white/90">
              <p>
                Scale:{" "}
                {dash.payment_monitor.monitor.scale.connected ? "🟢 API OK" : "⚪ нет ключа"}{" "}
                · задач: {dash.payment_monitor.monitor.scale.live_tasks ? "есть" : "нет"}
                {dash.payment_monitor.monitor.scale.task_count
                  ? ` (${dash.payment_monitor.monitor.scale.task_count})`
                  : ""}
              </p>
              <p>
                Toloka:{" "}
                {dash.payment_monitor.monitor.toloka.connected ? "🟢 Pipeline API OK" : "⚪ нет ключа"}{" "}
                · проекты: {dash.payment_monitor.monitor.toloka.live_tasks ? "есть" : "нет"}
                {dash.payment_monitor.monitor.toloka.task_count != null
                  ? ` (${dash.payment_monitor.monitor.toloka.task_count})`
                  : ""}
              </p>
            </div>
            {dash.payment_monitor.payout?.has_withdraw_ready ? (
              <div className="mt-3 rounded-lg border border-amber-400/40 bg-amber-950/30 p-3 text-sm text-amber-100">
                {dash.payment_monitor.payout.pending_alerts?.[0]?.message}
              </div>
            ) : null}
            {dash.last_live_connection_test ? (
              <p
                className={`mt-2 text-xs ${
                  dash.last_live_connection_test.ok ? "text-emerald-300" : "text-rose-300"
                }`}
              >
                Live test: {dash.last_live_connection_test.ok ? "✅ OK" : "❌ FAIL"} —{" "}
                {dash.last_live_connection_test.log_line ?? dash.last_live_connection_test.message}
                {!dash.last_live_connection_test.ok && dash.payment_monitor.monitor.toloka.connected ? (
                  <span className="block mt-1 text-amber-200/90">
                    Toloka уже 🟢 — нажми «test_connection_live» ещё раз после перезапуска Genesis.exe
                    (старый FAIL мог остаться в журнале).
                  </span>
                ) : null}
              </p>
            ) : dash?.dry_run?.active ? (
              <p className="mt-2 text-xs text-sky-200/80">
                Live test работает только при FARM_LIVE_MODE=live. Сейчас dry-run — используй «Боевой
                тест» ниже.
              </p>
            ) : null}
          </section>
        ) : null}

        {dash?.payout_guide ? (
          <section className="genesis-card border-violet-500/25 p-4">
            <h2 className="text-sm font-semibold text-white">{dash.payout_guide.title}</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">{dash.payout_guide.note}</p>
            <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-white/85">
              {farmList(dash.payout_guide.steps).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>
          </section>
        ) : null}

        {dash?.revenue_forecast ? (
          <section className="genesis-card border-sky-500/20 bg-sky-950/10 p-5">
            <h2 className="text-sm font-bold text-sky-100">Прогноз (математика, не гарантия)</h2>
            <p className="mt-1 text-xs text-sky-200/70">{dash.revenue_forecast.disclaimer}</p>
            <p className="mt-3 text-sm text-white">
              50 нод × 10 ч: ~<strong>{formatEur(dash.revenue_forecast.labeling_swarm_10h.net_eur)}</strong> чистыми
              · сутки: ~<strong>{formatEur(dash.revenue_forecast.labeling_swarm_per_day.net_eur)}</strong>
            </p>
            {dash.last_battle_test ? (
              <p className="mt-2 text-xs text-emerald-200">
                Последний боевой тест: +{dash.last_battle_test.earned_eur.toFixed(4)} € ·{" "}
                {dash.last_battle_test.tasks_done} задач · {dash.last_battle_test.execution_target} · ~
                {dash.last_battle_test.pay_per_task_eur.toFixed(4)} €/задача
              </p>
            ) : null}
            <ul className="mt-3 space-y-1 text-xs text-genesis-muted">
              {farmList(dash.revenue_forecast.phases).map((p) => (
                <li key={p.label}>
                  <strong>{p.label}</strong>: {p.eur_per_day} €/день — {p.note}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {dash && (
          <section className="genesis-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs text-genesis-muted">{dash.balance_label}</p>
                <p className="mt-1 text-4xl font-bold tabular-nums text-emerald-300">
                  {formatEur(dash.total_earned_eur)}
                </p>
                <p className="mt-2 text-sm text-white/80">
                  Сегодня: <strong>{formatEur(dash.today_earned_eur)}</strong> · Задач:{" "}
                  <strong>{dash.total_tasks_done}</strong>
                </p>
                <p className="mt-1 text-xs text-genesis-muted">{dash.cost_ratio_note}</p>
              </div>
              <div className="text-right text-xs">
                <p
                  className={`inline-flex rounded-full px-3 py-1 font-semibold ${
                    dash.running ? "bg-emerald-500/20 text-emerald-200" : "bg-white/10 text-genesis-muted"
                  }`}
                >
                  {dash.running ? `${dash.workers_active} комбайнов` : "Остановлена"}
                </p>
                <p className="mt-2 text-genesis-muted">
                  Биржи: {connectedPlatforms}/{totalPlatforms} подключено
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <label className="text-xs text-genesis-muted">
                Комбайнов:
                <input
                  type="number"
                  min={1}
                  max={1000}
                  value={workers}
                  onChange={(e) => setWorkers(Number(e.target.value) || 10)}
                  className="ml-2 w-20 rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1 text-sm text-white"
                />
              </label>
              {!dash.running ? (
                <button
                  type="button"
                  disabled={busy === "start"}
                  onClick={() => void startFarm()}
                  className="rounded-xl bg-emerald-600 px-6 py-3 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
                >
                  {busy === "start" ? "Запуск…" : "▶ Запустить ферму"}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busy === "stop"}
                  onClick={() => void stopFarm()}
                  className="rounded-xl bg-rose-700 px-6 py-3 text-sm font-bold text-white hover:bg-rose-600 disabled:opacity-50"
                >
                  ⏸ Остановить
                </button>
              )}
              <button
                type="button"
                disabled={busy === "battle"}
                onClick={() => void runBattleTest()}
                className="rounded-xl border border-violet-500/40 bg-violet-950/30 px-4 py-3 text-sm font-semibold text-violet-100 hover:bg-violet-900/40 disabled:opacity-50"
              >
                {busy === "battle" ? "Тест…" : "⚔ Боевой тест (dry-run)"}
              </button>
              <button
                type="button"
                disabled={busy === "live"}
                onClick={() => void runLiveConnectTest()}
                className="rounded-xl border border-emerald-500/40 bg-emerald-950/30 px-4 py-3 text-sm font-semibold text-emerald-100 hover:bg-emerald-900/40 disabled:opacity-50"
              >
                {busy === "live" ? "Live…" : "🔗 test_connection_live"}
              </button>
            </div>
            {message ? <p className="mt-4 text-sm text-emerald-200">{message}</p> : null}
          </section>
        )}

        {dash && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold text-white">Биржи разметки (8 площадок)</h2>
            <p className="mt-1 text-xs text-genesis-muted">
              Genesis видит список. Подключение — только после твоей регистрации и ключа в .env.local.
            </p>
            <ul className="mt-4 space-y-4">
              {farmList(dash.platforms).map((p) => (
                <li
                  key={p.id}
                  className={`rounded-xl border px-4 py-3 ${
                    p.connected ? "border-emerald-500/30 bg-emerald-950/15" : "border-white/10"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-medium text-white">{p.label}</span>
                    <span className={`text-xs ${p.connected ? "text-emerald-400" : "text-amber-400"}`}>
                      {p.status_label}
                      {p.pay_hint ? ` · ${p.pay_hint}` : ""}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-genesis-muted">{p.note}</p>
                  {p.steps && p.steps.length > 0 && !p.connected ? (
                    <ol className="mt-2 list-decimal space-y-1 pl-4 text-[11px] text-amber-100/80">
                      {farmList(p.steps).map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  ) : null}
                  {p.env_var && !p.connected ? (
                    <p className="mt-2 font-mono text-[10px] text-violet-200">
                      .env.local → {p.env_var}=твой_ключ
                    </p>
                  ) : null}
                  {p.signup_url && !p.connected ? (
                    <a
                      href={p.signup_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-[11px] text-sky-300 underline"
                    >
                      Открыть регистрацию →
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        )}

        {dash && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold text-white">Последние задачи</h2>
            <p className="mt-1 text-[11px] text-genesis-muted">
              Задача принята → выполнена → оплата → баланс · жёлтый = Scale пропущен
            </p>
            {!farmList(dash.recent_tasks).length ? (
              <p className="mt-3 text-sm text-genesis-muted">Пусто — жми «Запустить ферму».</p>
            ) : (
              <ul className="mt-3 max-h-72 space-y-2 overflow-y-auto text-xs">
                {farmList(dash.recent_tasks).map((t) => (
                  <li
                    key={t.id}
                    className={`rounded-lg border px-3 py-2 ${lifecycleRowClass(t.lifecycle_stage)}`}
                  >
                    <div className="flex flex-wrap justify-between gap-2">
                      <span className="text-white/90">
                        <span className="font-medium text-white">{lifecycleTitle(t)}</span>
                        <span className="text-genesis-muted"> · {ADAPTER_LABELS[t.adapter] ?? t.adapter}</span>
                      </span>
                      <span className={taskTone(t)}>
                        {showPayAmount(t) ? `+${t.pay_eur.toFixed(4)} € · ` : ""}
                        {t.detail}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {dash ? (
          <p className="text-center text-[11px] leading-relaxed text-genesis-muted">{dash.honesty_note}</p>
        ) : null}
      </div>
    </main>
  );
}
