"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur, formatLocalizedMoney } from "../lib/formatEur";

import { BRAND_NAME } from "../lib/publicBrand";

/** CEO desk is local-only (backend guard). Always hit the API host, not Next rewrite. */
const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

function apiErrorText(body: unknown, status: number, fallback: string): string {
  if (body && typeof body === "object") {
    const d = (body as { detail?: unknown; message_ru?: unknown }).detail;
    const mr = (body as { message_ru?: unknown }).message_ru;
    if (typeof mr === "string" && mr.trim()) return mr;
    if (typeof d === "string" && d.trim()) return d;
    if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
      return String((d[0] as { msg: unknown }).msg);
    }
  }
  if (status === 404) return "API не найден — перезапустите backend (Genesis.exe → Запустить)";
  if (status === 0 || status >= 500) return `${fallback} (HTTP ${status || "сеть"})`;
  return `${fallback} (HTTP ${status})`;
}

function formatDeskDelta(body: {
  message_ru?: string;
  desk_action?: {
    at?: string;
    summary_ru?: string;
    metrics?: Record<string, unknown>;
  };
}): string {
  const base = String(body.message_ru || "").trim();
  const da = body.desk_action;
  if (!da) return base;
  const m = da.metrics || {};
  const bits: string[] = [];
  if (m.created != null) bits.push(`новые=${m.created}`);
  if (m.drafted != null) bits.push(`draft=${m.drafted}`);
  if (m.prepared != null) bits.push(`prepare=${m.prepared}`);
  if (m.rebuilt != null) bits.push(`писем=${m.rebuilt}`);
  if (m.repriced != null) bits.push(`цены=${m.repriced}`);
  if (m.sent_today_total != null) bits.push(`sent_today=${m.sent_today_total}`);
  if (m.wallet_available != null) bits.push(`wallet=${m.wallet_available}`);
  if (m.pipeline_count != null) bits.push(`pipeline=${m.pipeline_count}`);
  if (m.pipeline_head_name) bits.push(`топ: ${m.pipeline_head_name}`);
  if (m.pipeline_head_pkg) bits.push(`pkg=${m.pipeline_head_pkg}`);
  if (m.pipeline_head_priority != null) bits.push(`priority=${m.pipeline_head_priority}`);
  const stamp = da.at ? ` · ⌚️ ${String(da.at).slice(11, 19)} UTC` : "";
  const delta = bits.length ? `Δ ${bits.join(" · ")}` : da.summary_ru || "";
  return [base, delta].filter(Boolean).join(" · ") + stamp;
}

const BUSY_LABELS: Record<string, string> = {
  refresh: "Обновляем лиды… запрос к API",
  rebuild: "Пересобираем квоты… запрос к API",
  "reset-desk": "Обнуляем счётчики… запрос к API",
  generate: "Генерируем черновики…",
  adaptive: "Недельный Adaptive-обзор…",
  "runner-start": "Запуск Country Desk…",
  "runner-stop": "Остановка…",
  "prefs-refresh": "Сохраняем автообновление…",
  "prefs-send": "Сохраняем автоотправку…",
};

type OutreachQuotaHealth = {
  daily_cap: number;
  hard_max: number;
  day?: string | null;
  domain_count: number;
  region_count?: number;
  pool_cap_total: number;
  sent_today_total: number;
  remaining_today_total: number;
  primary_used_today: number;
  primary_remaining: number;
  regions?: {
    region: string;
    label_ru: string;
    used_today: number;
    remaining: number;
    at_cap: boolean;
    daily_cap: number;
    domains?: { from?: string; domain: string; used_today: number }[];
  }[];
  markets?: {
    code: string;
    flag?: string;
    name_ru: string;
    enabled: boolean;
    phase: number;
    daily_cap: number;
    used_today: number;
    remaining: number;
    at_cap: boolean;
  }[];
  domains: {
    from?: string;
    domain: string;
    region?: string;
    used_today: number;
    remaining: number;
    at_cap: boolean;
  }[];
  global_daily_cap?: number;
  min_interval_sec?: number;
  delivery_eta_minutes?: number;
  phase_note_ru?: string;
  sniper_note_ru?: string;
};

type AdaptiveOutreach = {
  enabled?: boolean;
  note_ru?: string;
  shared_global?: boolean;
  global_daily_cap?: number;
  current_health?: number;
  current_health_label?: string;
  scaling_status?: string;
  next_review_at?: string | null;
  last_review_at?: string | null;
  interval_sec?: number;
  paused_markets?: string[];
  roi_note_ru?: string;
  roi_table?: {
    code: string;
    flag?: string;
    name_ru: string;
    spent_eur: number;
    orders: number;
    revenue_eur: number;
    roi: number | null;
    paused?: boolean;
  }[];
  countries?: {
    code: string;
    flag?: string;
    name_ru: string;
    current_cap: number;
    recommended_cap: number;
    scaling_status: string;
    paused?: boolean;
    spent_eur?: number;
    roi?: number | null;
    health: { score: number; label: string; reasons?: string[] };
  }[];
  last_decisions?: {
    code: string;
    decision: string;
    from_cap: number;
    to_cap: number;
    reason: string;
    applied?: boolean;
  }[];
  history?: { at: string; decisions?: { code: string; decision: string; from_cap: number; to_cap: number }[] }[];
  graphs?: {
    days?: string[];
    daily_emails?: number[];
    reply_rate?: (number | null)[];
    bounce_rate?: (number | null)[];
    orders?: number[];
    revenue?: number[];
    health_score?: (number | null)[];
    note_ru?: string;
  };
};

type OutreachRunner = {
  running?: boolean;
  ticks?: number;
  session_leads?: number;
  session_drafts?: number;
  session_sends?: number;
  session_skipped?: number;
  last_message_ru?: string | null;
  last_tick_at?: string | null;
  next_tick_at?: string | null;
  interval_sec?: number;
  outreach_send_enabled?: boolean;
  note_ru?: string;
  log?: { at: string; action: string; message_ru: string }[];
};

type MarketsDashboard = {
  note_ru?: string;
  delivery_eta_minutes?: number;
  allocation_mode?: string;
  quality_first?: boolean;
  force_fill_quotas?: boolean;
  global_daily_cap?: number;
  min_interval_sec?: number;
  sent_today_total?: number;
  remaining_today_total?: number;
  enabled_count?: number;
  planned_count?: number;
  table: {
    code: string;
    flag?: string;
    name_ru: string;
    enabled: boolean;
    phase: number;
    daily_cap: number;
    sent_today: number;
    replies: number;
    orders: number;
    currency?: string;
    symbol?: string;
    basic_price_label?: string;
    business_price_label?: string;
    premium_price_label?: string;
    delivery_eta_minutes?: number;
    hubs?: string[];
    language?: string;
    legal_profile?: string;
  }[];
};

type StudioStatus = {
  version: string;
  name: string;
  auto_search: boolean;
  auto_refresh?: boolean;
  auto_send: boolean;
  outreach_send_enabled: boolean;
  outreach_send_note: string;
  law: string;
  pending_approval_count: number;
  sent_count: number;
  pipeline_count: number;
  manual_review_count?: number;
  auto_draft_max_eur?: number;
  outreach_daily_cap?: number;
  outreach_quota?: OutreachQuotaHealth | null;
  markets_dashboard?: MarketsDashboard | null;
  adaptive_outreach?: AdaptiveOutreach | null;
  outreach_runner?: OutreachRunner | null;
  last_desk_action?: {
    action?: string;
    at?: string;
    summary_ru?: string;
    metrics?: Record<string, unknown>;
  } | null;
  ranking_goal_ru?: string;
  pilot_catalog?: {
    checkout_online: string[];
    pilot_quote: string[];
    horizon: string[];
    note?: string;
    sales_modes?: { auto?: string; expert?: string };
    focus_niches_de?: { id: string; label: string; examples: string }[];
    offer_formula_de?: string;
  };
};

type QueueItem = {
  id: string;
  company_name: string;
  contact: string;
  website_url: string;
  recommended_price_eur: number;
  recommended_currency?: string;
  recommended_price_label?: string;
  recommended_package_id: string;
  email_subject: string;
  proposed_message: string;
  fit_reason: string;
  pricing_rationale: string;
  issue_count: number;
  site_issues?: string[];
  suggested_services?: string[];
  score: number;
  outreach_status?: string | null;
  price_tier?: string | null;
  crm_status?: string | null;
  last_market_lesson?: string | null;
};

type Evidence = {
  sample_size: number;
  contacted: number;
  replied: number;
  won: number;
  reply_rate_pct: number;
  insights: string[];
  recent_lessons?: {
    company?: string;
    event?: string;
    reason?: string;
    reason_label_ru?: string;
    comment?: string;
    lesson?: string;
    at?: string;
  }[];
  reason_counts?: { reason: string; label_ru: string; count: number }[];
  learning?: {
    sent: number;
    lessons_logged: number;
    pending_lessons: number;
    completeness_pct: number;
  };
  evidence_ready: boolean;
  note: string;
  milestone_ru?: string;
};

type Worklist = {
  date: string;
  mode: string;
  note: string;
  target_per_day: number;
  segments: { id: string; label: string; cities: string[]; signals: string[] }[];
  target_city?: string;
  search_radius?: number;
  profitable_niches?: string[];
  outreach_daily_cap?: number;
  outreach_quota?: OutreachQuotaHealth | null;
};

type InboundLead = {
  id: string;
  company_name: string;
  contact: string;
  fit_reason: string;
  score: number;
  potential_value_eur: number;
  found_at: string;
  notes?: string;
};

type GateFunnel = {
  title_ru?: string;
  hint_ru?: string;
  bottleneck_ru?: string;
  pulse_ru?: string;
  stages?: { id: string; label_ru: string; count: number }[];
  summary?: Record<string, number>;
};

type PipelineLead = QueueItem & {
  status?: string;
  status_label?: string;
  source_id?: string;
  win_probability_pct?: number | null;
  niche?: string | null;
  market?: string | null;
  hunt_city?: string | null;
  quality_archive?: boolean;
  lead_priority?: number | null;
  business_potential?: number | null;
  website_need?: number | null;
  expected_value_eur?: number | null;
  commercial_niche?: string | null;
};

export default function AcquisitionPage() {
  const [status, setStatus] = useState<StudioStatus | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [pipeline, setPipeline] = useState<PipelineLead[]>([]);
  const [inboundLeads, setInboundLeads] = useState<InboundLead[]>([]);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [worklist, setWorklist] = useState<Worklist | null>(null);
  const [funnel, setFunnel] = useState<GateFunnel | null>(null);
  const [selected, setSelected] = useState<QueueItem | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [actionOk, setActionOk] = useState<boolean | null>(null);

  function flash(text: string, ok: boolean | null = null) {
    setMessage(text);
    setActionOk(ok);
  }
  const [lawfulConfirmed, setLawfulConfirmed] = useState(false);
  const [siteProblemOk, setSiteProblemOk] = useState(false);
  const [benefitOk, setBenefitOk] = useState(false);
  const [wouldSendOk, setWouldSendOk] = useState(false);
  const [lawfulNote, setLawfulNote] = useState("");
  const [marketLesson, setMarketLesson] = useState("");
  const [marketReason, setMarketReason] = useState("no_reply");
  const [outcomeEvent, setOutcomeEvent] = useState("no_reply");
  const [learnLeadId, setLearnLeadId] = useState("");
  const [genCity, setGenCity] = useState("Köln");
  const [genQuery, setGenQuery] = useState("Kfz-Werkstatt");
  const [genLimit, setGenLimit] = useState(10);
  const [forceSkipCheck, setForceSkipCheck] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [st, q, ev, wl, inbox, gf, pipe] = await Promise.all([
        fetch(`${API}/api/acquisition/status`),
        fetch(`${API}/api/acquisition/approval-queue`),
        fetch(`${API}/api/acquisition/evidence`),
        fetch(`${API}/api/acquisition/worklist`),
        fetch(`${API}/api/leads/inbox?today_only=true&limit=20`),
        fetch(`${API}/api/acquisition/gate-funnel`),
        fetch(`${API}/api/acquisition/pipeline?limit=50`),
      ]);
      if (st.ok) setStatus(await st.json());
      if (q.ok) {
        const body = await q.json();
        const items = body.items ?? [];
        setQueue(items);
        setSelected((prev) => items.find((i: QueueItem) => i.id === prev?.id) ?? items[0] ?? null);
      }
      if (ev.ok) setEvidence(await ev.json());
      if (wl.ok) {
        const w = await wl.json();
        setWorklist(w);
        if (w.target_city) setGenCity(String(w.target_city));
        if (Array.isArray(w.profitable_niches) && w.profitable_niches[0]) {
          setGenQuery(String(w.profitable_niches[0]));
        }
      }
      if (inbox.ok) {
        const body = await inbox.json();
        setInboundLeads(body.leads ?? []);
      }
      if (gf.ok) setFunnel(await gf.json());
      if (pipe.ok) {
        const body = await pipe.json();
        setPipeline(body.items ?? []);
      }
    } catch {
      flash(
        `Не удалось загрузить Studio. Backend ${API} не отвечает — Genesis.exe → Запустить.`,
        false,
      );
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const runner = status?.outreach_runner;
  const runnerRunning = Boolean(runner?.running);

  useEffect(() => {
    if (!runnerRunning) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const res = await fetch(`${API}/api/acquisition/runner/tick`, { method: "POST" });
        const body = await res.json();
        if (cancelled) return;
        if (body.last_message_ru) setMessage(String(body.last_message_ru));
        await refresh();
      } catch {
        /* keep polling */
      }
    };
    void tick();
    const intervalMs = Math.max(15, Number(runner?.interval_sec || 90)) * 1000;
    const id = window.setInterval(() => void tick(), intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [runnerRunning, runner?.interval_sec, refresh]);

  async function approve(id: string) {
    setBusy(id);
    setMessage("");
    try {
      if (!siteProblemOk) {
        setMessage("Нужно: конкретная проблема именно этого сайта (не общая фраза).");
        return;
      }
      if (!benefitOk) {
        setMessage("Нужно: понятная польза именно для этого бизнеса.");
        return;
      }
      if (!wouldSendOk) {
        setMessage("Нужно: вы сами отправили бы такое письмо владельцу этой компании?");
        return;
      }
      if (!lawfulConfirmed) {
        setMessage("Нужно: самостоятельно проверить законность контакта.");
        return;
      }
      const res = await fetch(`${API}/api/acquisition/opportunities/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event: "lawful_basis",
          note: [
            lawfulNote.trim(),
            "ceo:site_problem",
            "ceo:benefit",
            "ceo:would_send",
            "ceo:lawful",
          ]
            .filter(Boolean)
            .join(" · "),
        }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Одобрено" : "Ошибка"));
      setSiteProblemOk(false);
      setBenefitOk(false);
      setWouldSendOk(false);
      setLawfulConfirmed(false);
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function recordMarketOutcome(id: string) {
    if (!marketReason) {
      setMessage("Выберите причину из списка.");
      return;
    }
    if (marketReason === "other" && !marketLesson.trim()) {
      setMessage("Для «Другое» нужен короткий комментарий.");
      return;
    }
    setBusy(id);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/acquisition/opportunities/${id}/interaction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event: outcomeEvent,
          note: "",
          market_reason: marketReason,
          market_lesson: marketLesson.trim(),
        }),
      });
      const body = await res.json();
      setMessage(
        res.ok
          ? body.message ?? "Урок рынка записан."
          : typeof body.detail === "string"
            ? body.detail
            : "Не удалось записать исход"
      );
      if (res.ok) {
        setMarketLesson("");
        setLearnLeadId("");
        await refresh();
      }
    } finally {
      setBusy("");
    }
  }

  async function refreshLeads() {
    setBusy("refresh");
    flash(`Запрос: POST ${API}/api/acquisition/refresh-leads …`, null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 90_000);
    try {
      const res = await fetch(`${API}/api/acquisition/refresh-leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          city: genCity,
          query: genQuery,
          limit: Math.min(genLimit, 6),
          auto_confirm: true,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        flash(formatDeskDelta(body), true);
        if (body.pipeline) setPipeline(body.pipeline);
        if (body.gate_funnel) setFunnel(body.gate_funnel);
        await refresh();
      } else {
        flash(apiErrorText(body, res.status, "Ошибка обновления лидов"), false);
      }
    } catch (err) {
      const aborted = err instanceof DOMException && err.name === "AbortError";
      flash(
        aborted
          ? "Обновление прервано по таймауту (90с)."
          : `Backend не отвечает (${API}). Genesis.exe → Запустить, затем снова «Обновить лиды».`,
        false,
      );
    } finally {
      window.clearTimeout(timeoutId);
      setBusy("");
    }
  }

  async function rebuildAllQuotes() {
    setBusy("rebuild");
    flash(`Запрос: POST ${API}/api/acquisition/rebuild-quotes …`, null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 120_000);
    try {
      const res = await fetch(`${API}/api/acquisition/rebuild-quotes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ limit: 80 }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        flash(formatDeskDelta(body), true);
        if (body.pipeline) setPipeline(body.pipeline);
        await refresh();
      } else {
        flash(apiErrorText(body, res.status, "Ошибка пересборки квот"), false);
      }
    } catch (err) {
      const aborted = err instanceof DOMException && err.name === "AbortError";
      flash(
        aborted
          ? "Пересборка прервана по таймауту. Перезапустите backend и попробуйте снова."
          : `Backend не отвечает (${API}). Genesis.exe → Запустить, затем снова «Пересобрать все квоты».`,
        false,
      );
    } finally {
      window.clearTimeout(timeoutId);
      setBusy("");
    }
  }

  async function resetDeskAndWallet() {
    if (
      !window.confirm(
        "Обнулить счётчики отправки за сегодня и кошелёк/ledger до 0? Лиды не удаляются.",
      )
    ) {
      return;
    }
    setBusy("reset-desk");
    flash(`Запрос: POST ${API}/api/acquisition/reset-desk …`, null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 30_000);
    try {
      const res = await fetch(`${API}/api/acquisition/reset-desk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({}),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        flash(formatDeskDelta(body), true);
        if (body.pipeline) setPipeline(body.pipeline);
        await refresh();
      } else {
        flash(apiErrorText(body, res.status, "Ошибка обнуления"), false);
      }
    } catch (err) {
      const aborted = err instanceof DOMException && err.name === "AbortError";
      flash(
        aborted
          ? "Обнуление прервано по таймауту."
          : `Backend не отвечает (${API}). Genesis.exe → Запустить.`,
        false,
      );
    } finally {
      window.clearTimeout(timeoutId);
      setBusy("");
    }
  }

  async function generateDrafts() {
    setBusy("generate");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/acquisition/generate-drafts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city: genCity,
          query: genQuery,
          limit: genLimit,
          language: "de",
          throttle_ms: 300,
          force_skip_check: forceSkipCheck,
        }),
      });
      const body = await res.json();
      setMessage(
        res.ok
          ? `Готово: leads=${body.leads_found ?? 0}, created=${body.created ?? 0}, drafted=${body.drafted ?? 0}, skipped_has_site=${body.skipped_has_site ?? 0}, already_queued=${body.skipped_already_queued ?? 0}`
          : body.detail ?? "Ошибка генерации"
      );
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function reject(id: string) {
    setBusy(id);
    await fetch(`${API}/api/acquisition/opportunities/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event: "rejected", note: "" }),
    });
    setMessage("Черновик отклонён.");
    refresh();
    setBusy("");
  }

  async function markSent(id: string) {
    setBusy(id);
    await fetch(`${API}/api/acquisition/opportunities/${id}/mark-sent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event: "sent_manual", note: "" }),
    });
    setMessage("Отмечено: отправлено вручную.");
    refresh();
    setBusy("");
  }

  function copyDraft(item: QueueItem) {
    const text = `Subject: ${item.email_subject}\n\n${item.proposed_message}`;
    navigator.clipboard.writeText(text);
    setMessage("Скопировано в буфер — отправьте из своего почтового клиента.");
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-4xl space-y-6">
        {(busy || message) && (
          <div
            role="status"
            className={`sticky top-2 z-40 rounded-xl border px-4 py-3 text-sm shadow-lg ${
              busy
                ? "border-sky-500/40 bg-sky-950/90 text-sky-50"
                : actionOk === false
                  ? "border-rose-500/50 bg-rose-950/90 text-rose-50"
                  : actionOk === true
                    ? "border-emerald-500/40 bg-emerald-950/90 text-emerald-50"
                    : "border-white/20 bg-black/85 text-white"
            }`}
          >
            <p className="font-medium">
              {busy ? BUSY_LABELS[busy] || `Выполняется: ${busy}…` : message}
            </p>
            {busy && message ? (
              <p className="mt-1 text-xs opacity-80">{message}</p>
            ) : null}
            {!busy && actionOk === false ? (
              <p className="mt-1 text-xs opacity-80">
                Это не «нет новых лидов» — запрос к API не удался. Проверьте Genesis.exe и Network.
              </p>
            ) : null}
          </div>
        )}
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">Mission 1.5</p>
          <h1 className="mt-2 text-2xl font-semibold">Country Desk · все рынки</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Пуск крутит hunt/draft round-robin по странам до их лимитов (adaptive паузы
            пропускаются). Ферма разметки отдельно на «Ферма». {status?.law}
          </p>
          {status && (
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <Badge ok={Boolean(status.auto_refresh) || runnerRunning}>
                {status.auto_refresh || runnerRunning ? "Автообновление вкл" : "Автообновление выкл"}
              </Badge>
              <Badge ok={status.auto_send || status.outreach_send_enabled}>
                {status.auto_send || status.outreach_send_enabled
                  ? "Автоотправка вкл"
                  : "Без автоотправки"}
              </Badge>
              <Badge ok>Локальные цены (CZK / UAH / USD / EUR…)</Badge>
              <Badge ok={(status.manual_review_count ?? 0) === 0}>
                Ручная проверка: {status.manual_review_count ?? 0}
              </Badge>
              <Badge ok={status.outreach_send_enabled}>Resend / send path</Badge>
              <span className="text-genesis-muted self-center">
                Одобрение: {status.pending_approval_count} · Отправлено: {status.sent_count}
              </span>
            </div>
          )}
          {status?.ranking_goal_ru ? (
            <p className="mt-3 text-xs text-emerald-200/80">{status.ranking_goal_ru}</p>
          ) : null}
          {status?.last_desk_action?.at ? (
            <p className="mt-2 rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-xs text-white/80">
              Последнее действие:{" "}
              <span className="text-emerald-300">{status.last_desk_action.action}</span>
              {" · "}
              {status.last_desk_action.summary_ru || "—"}
              {" · "}
              {String(status.last_desk_action.at).replace("T", " ").slice(0, 19)} UTC
            </p>
          ) : null}
          {status?.pilot_catalog && (
            <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-genesis-muted">
              <div>
                <p className="font-medium text-white/90">Две модели продаж</p>
                <p className="mt-1">
                  <span className="text-emerald-300">Auto:</span>{" "}
                  {status.pilot_catalog.sales_modes?.auto ?? "Лендинг /order"}
                </p>
                <p className="mt-0.5">
                  <span className="text-sky-300">Expert:</span>{" "}
                  {status.pilot_catalog.sales_modes?.expert ?? "Пилот · запрос"}
                </p>
              </div>
              {status.pilot_catalog.offer_formula_de && (
                <p className="rounded-lg border border-emerald-500/20 bg-emerald-950/20 p-2 text-emerald-100/90">
                  {status.pilot_catalog.offer_formula_de}
                </p>
              )}
              <div>
                <p className="font-medium text-white/90">Каталог</p>
                <p className="mt-1">
                  Оплата: {(status.pilot_catalog.checkout_online || []).join(", ")} · Запрос:{" "}
                  {(status.pilot_catalog.pilot_quote || []).slice(0, 5).join(", ")}
                  {(status.pilot_catalog.pilot_quote || []).length > 5 ? "…" : ""}
                </p>
              </div>
              {status.pilot_catalog.focus_niches_de && status.pilot_catalog.focus_niches_de.length > 0 && (
                <div>
                  <p className="font-medium text-white/90">Фокус-ниши</p>
                  <p className="mt-1">
                    {status.pilot_catalog.focus_niches_de.map((n) => n.label).join(" · ")}
                  </p>
                </div>
              )}
              <Link href="/services" className="inline-block text-emerald-300 hover:underline">
                Публичные услуги /services →
              </Link>
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              disabled={busy === "prefs-refresh"}
              onClick={() => {
                void (async () => {
                  setBusy("prefs-refresh");
                  setMessage("");
                  try {
                    const next = !(status?.auto_refresh || runnerRunning);
                    const res = await fetch(`${API}/api/acquisition/ceo-prefs`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ auto_refresh: next }),
                    });
                    const body = await res.json();
                    setMessage(
                      next
                        ? "Автообновление включено · после Пуска runner будет охотиться по странам"
                        : "Автообновление выключено",
                    );
                    await refresh();
                    void body;
                  } finally {
                    setBusy("");
                  }
                })();
              }}
              className="rounded-lg border border-sky-500/40 bg-sky-950/30 px-3 py-1.5 font-medium text-sky-100 hover:bg-sky-900/40 disabled:opacity-50"
            >
              {status?.auto_refresh || runnerRunning ? "⏸ Автообновление" : "🔄 Автообновление"}
            </button>
            <button
              type="button"
              disabled={busy === "prefs-send"}
              onClick={() => {
                void (async () => {
                  setBusy("prefs-send");
                  setMessage("");
                  try {
                    const next = !Boolean(status?.auto_send);
                    const res = await fetch(`${API}/api/acquisition/ceo-prefs`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ auto_send: next }),
                    });
                    const body = await res.json();
                    setMessage(
                      next
                        ? "Автоотправка включена · тики будут слать Approve/high-win (нужен Resend)"
                        : "Автоотправка выключена",
                    );
                    await refresh();
                    void body;
                  } finally {
                    setBusy("");
                  }
                })();
              }}
              className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 font-medium text-amber-100 hover:bg-amber-900/40 disabled:opacity-50"
            >
              {status?.auto_send ? "⏹ Автоотправка" : "▶ Автоотправка"}
            </button>
            <button
              type="button"
              disabled={busy === "runner-start" || runnerRunning}
              onClick={() => {
                void (async () => {
                  setBusy("runner-start");
                  setMessage("");
                  try {
                    const res = await fetch(`${API}/api/acquisition/runner/start`, {
                      method: "POST",
                    });
                    const body = await res.json();
                    setMessage(body.last_message_ru || "Country Desk запущен");
                    await refresh();
                  } finally {
                    setBusy("");
                  }
                })();
              }}
              className="rounded-lg border border-emerald-500/50 bg-emerald-950/40 px-3 py-1.5 font-medium text-emerald-100 hover:bg-emerald-900/40 disabled:opacity-50"
            >
              {busy === "runner-start" ? "Пуск…" : "▶ Пуск"}
            </button>
            <button
              type="button"
              disabled={busy === "runner-stop" || !runnerRunning}
              onClick={() => {
                void (async () => {
                  setBusy("runner-stop");
                  setMessage("");
                  try {
                    const res = await fetch(`${API}/api/acquisition/runner/stop`, {
                      method: "POST",
                    });
                    const body = await res.json();
                    setMessage(body.last_message_ru || "Остановлено");
                    await refresh();
                  } finally {
                    setBusy("");
                  }
                })();
              }}
              className="rounded-lg border border-rose-500/50 bg-rose-950/30 px-3 py-1.5 font-medium text-rose-100 hover:bg-rose-900/40 disabled:opacity-50"
            >
              {busy === "runner-stop" ? "Стоп…" : "⏹ Стоп"}
            </button>
            <button
              type="button"
              disabled={busy === "refresh"}
              onClick={() => void refreshLeads()}
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40 disabled:opacity-50"
            >
              {busy === "refresh" ? "Генерация…" : "Один цикл · hunt"}
            </button>
            <button
              type="button"
              disabled={busy === "adaptive"}
              onClick={() => {
                void (async () => {
                  setBusy("adaptive");
                  setMessage("");
                  try {
                    const res = await fetch(`${API}/api/acquisition/adaptive/review`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ force: true, apply: true }),
                    });
                    const body = await res.json();
                    setMessage(
                      body.skipped
                        ? "Adaptive: обзор ещё не пора"
                        : `Adaptive review: ${ (body.decisions || []).length } стран`
                    );
                    refresh();
                  } finally {
                    setBusy("");
                  }
                })();
              }}
              className="rounded-lg border border-sky-500/40 px-3 py-1.5 text-sky-100 hover:bg-sky-950/30 disabled:opacity-50"
            >
              {busy === "adaptive" ? "Обзор…" : "Недельный Adaptive-обзор"}
            </button>
            <Link
              href="/#lost-archive"
              className="rounded-lg border border-rose-500/40 px-3 py-1.5 text-rose-100 hover:bg-rose-950/30"
            >
              Архив отказов
            </Link>
            <Link
              href="/"
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40"
            >
              Ферма разметки
            </Link>
            <Link
              href="/journal"
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40"
            >
              Журнал
            </Link>
          </div>
          {runner ? (
            <div
              className={`mt-3 rounded-lg border px-3 py-2 text-xs ${
                runnerRunning
                  ? "border-emerald-500/40 bg-emerald-950/20 text-emerald-100"
                  : "border-genesis-border bg-genesis-elevated/20 text-genesis-muted"
              }`}
            >
              <p className="font-medium text-white/90">
                {runnerRunning ? "● Работает" : "○ Остановлен"} · тиков {runner.ticks ?? 0} · лиды{" "}
                {runner.session_leads ?? 0} · черновики {runner.session_drafts ?? 0} · отправки{" "}
                {runner.session_sends ?? 0} · пропуски {runner.session_skipped ?? 0} · интервал ~
                {runner.interval_sec ?? "—"}с
              </p>
              <p className="mt-1">{runner.last_message_ru || runner.note_ru}</p>
              {runner.log && runner.log.length > 0 ? (
                <ul className="mt-2 max-h-28 space-y-0.5 overflow-y-auto text-[11px] text-white/70">
                  {[...runner.log].reverse().slice(0, 8).map((e) => (
                    <li key={`${e.at}-${e.action}`}>
                      {String(e.at).slice(11, 19)} · {e.action}: {e.message_ru}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </header>

        {funnel?.stages ? (
          <section className="genesis-card space-y-3 p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-sm font-semibold">{funnel.title_ru ?? "Пульс гейтов"}</h2>
              <p className="text-[11px] text-amber-200/80">Затык: {funnel.bottleneck_ru ?? "—"}</p>
            </div>
            <p className="text-xs text-genesis-muted">{funnel.hint_ru}</p>
            <div className="flex flex-wrap gap-2">
              {funnel.stages.map((s) => (
                <div
                  key={s.id}
                  className="min-w-[6.5rem] rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-center"
                >
                  <p className="text-[10px] uppercase tracking-wide text-white/50">{s.label_ru}</p>
                  <p className="mt-1 text-xl font-semibold tabular-nums text-white">{s.count}</p>
                </div>
              ))}
            </div>
            {funnel.pulse_ru ? (
              <p className="text-[11px] leading-relaxed text-white/60">{funnel.pulse_ru}</p>
            ) : null}
          </section>
        ) : null}

        {status && !status.outreach_send_enabled && (
          <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-xs text-amber-100/90">
            {status.outreach_send_note}
          </p>
        )}

        {(status?.outreach_quota || worklist?.outreach_quota) && (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold">Квота отправки · рынки сегодня</h2>
            {(() => {
              const q = status?.outreach_quota || worklist?.outreach_quota;
              if (!q) return null;
              const cap = q.daily_cap;
              const marketCards = (q.markets || []).filter((m) => m.enabled);
              const regions = marketCards.length
                ? marketCards.map((m) => ({
                    region: m.code,
                    label_ru: `${m.flag || ""} ${m.name_ru}`.trim(),
                    used_today: m.used_today,
                    remaining: m.remaining,
                    at_cap: m.at_cap,
                    daily_cap: m.daily_cap,
                  }))
                : q.regions?.length
                  ? q.regions
                  : [
                      {
                        region: "de",
                        label_ru: "Германия",
                        used_today: q.primary_used_today,
                        remaining: q.primary_remaining,
                        at_cap: q.primary_remaining <= 0,
                        daily_cap: cap,
                      },
                    ];
              return (
                <>
                  <div className="rounded-xl border border-emerald-500/35 bg-emerald-950/30 px-4 py-4">
                    <p className="text-[11px] uppercase tracking-wide text-emerald-200/80">
                      Дневной потолок Virtus · все рынки
                    </p>
                    <p className="mt-1 text-3xl font-semibold tabular-nums text-white">
                      {q.sent_today_total ?? 0}{" "}
                      <span className="text-lg font-normal text-white/50">/</span>{" "}
                      {q.global_daily_cap ?? q.pool_cap_total ?? cap}
                    </p>
                    <p className="mt-1 text-xs text-genesis-muted">
                      осталось{" "}
                      {q.remaining_today_total ??
                        Math.max(
                          0,
                          Number(q.global_daily_cap ?? q.pool_cap_total ?? cap) -
                            Number(q.sent_today_total || 0),
                        )}
                      {q.min_interval_sec != null
                        ? ` · интервал ≥ ${q.min_interval_sec}с`
                        : ""}
                    </p>
                    <p className="mt-2 text-xs font-medium text-emerald-100/90">
                      Срок поставки сайта после оплаты: ≈{q.delivery_eta_minutes ?? 15} минут — для
                      всех стран
                    </p>
                  </div>
                  <div className="max-h-48 overflow-y-auto">
                    <div className="grid gap-2 text-sm sm:grid-cols-3">
                      {regions.map((r) => (
                        <p
                          key={r.region}
                          className="rounded-lg border border-genesis-border-subtle bg-black/20 px-3 py-2"
                        >
                          <span className="text-genesis-muted">{r.label_ru}</span>
                          <span className="mt-1 block font-medium text-white">
                            {r.used_today} / {r.daily_cap ?? cap}
                            {r.at_cap ? (
                              <span className="ml-1 text-xs font-normal text-amber-300">
                                лимит
                              </span>
                            ) : null}
                          </span>
                          <span className="mt-0.5 block text-[11px] text-genesis-muted">
                            осталось {r.remaining}
                          </span>
                        </p>
                      ))}
                    </div>
                  </div>
                  {q.domains?.length ? (
                    <ul className="space-y-1 text-xs text-genesis-muted">
                      {q.domains.map((d) => (
                        <li key={`${d.region || "de"}-${d.domain || d.from || "x"}`}>
                          {(d.region || "de").toUpperCase()} · {d.domain || "—"}:{" "}
                          {d.used_today} (регион {d.at_cap ? "лимит" : "ok"})
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-genesis-muted">
                      From не настроены. Пример:{" "}
                      <code className="text-white/70">
                        de:…@de.de, cis:…@cis.com, us:…@us.com
                      </code>
                    </p>
                  )}
                  {q.phase_note_ru ? (
                    <p className="text-[11px] leading-relaxed text-emerald-200/80">{q.phase_note_ru}</p>
                  ) : null}
                  {q.sniper_note_ru ? (
                    <p className="text-[11px] leading-relaxed text-genesis-muted">{q.sniper_note_ru}</p>
                  ) : null}
                  <p className="text-[11px] text-genesis-muted">
                    Лимит/день на рынок:{" "}
                    <code className="text-white/80">GENESIS_OUTREACH_DAILY_CAP</code> = {cap} · мир:{" "}
                    <code className="text-white/80">GENESIS_OUTREACH_GLOBAL_DAILY_CAP</code> ={" "}
                    {q.global_daily_cap ?? "—"}. Шаблоны:{" "}
                    <code className="text-white/80">GET /api/acquisition/outreach-templates</code>
                  </p>
                </>
              );
            })()}
          </section>
        )}

        {status?.markets_dashboard?.table?.length ? (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold">Рынки · старт-квота / отправлено / ответы / заказы</h2>
            <p className="text-xs text-genesis-muted">
              {status.markets_dashboard.note_ru ||
                "Стартовые квоты по странам · только качественные лиды · не заполняем любой ценой."}{" "}
              Срок сайта после оплаты: ≈
              {status.markets_dashboard.delivery_eta_minutes ?? 15} мин (все страны). mode=
              {status.markets_dashboard.allocation_mode || "per_market"} · quality_first=
              {String(status.markets_dashboard.quality_first ?? true)} · Вкл:{" "}
              {status.markets_dashboard.enabled_count ?? 0} · план:{" "}
              {status.markets_dashboard.planned_count ?? 0}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[46rem] text-left text-xs">
                <thead className="text-genesis-muted">
                  <tr className="border-b border-genesis-border-subtle">
                    <th className="py-2 pr-2 font-medium">Страна</th>
                    <th className="py-2 pr-2 font-medium">Валюта</th>
                    <th className="py-2 pr-2 font-medium">Basic</th>
                    <th className="py-2 pr-2 font-medium">Срок</th>
                    <th className="py-2 pr-2 font-medium">Лимит</th>
                    <th className="py-2 pr-2 font-medium">Отправлено</th>
                    <th className="py-2 pr-2 font-medium">Ответы</th>
                    <th className="py-2 pr-2 font-medium">Заказы</th>
                    <th className="py-2 font-medium">Фаза</th>
                  </tr>
                </thead>
                <tbody>
                  {status.markets_dashboard.table.map((row) => (
                    <tr
                      key={row.code}
                      className={`border-b border-white/5 ${
                        row.enabled ? "text-white/90" : "text-genesis-muted/70"
                      }`}
                    >
                      <td className="py-2 pr-2">
                        {row.flag} {row.name_ru}
                        {!row.enabled ? (
                          <span className="ml-1 text-[10px] uppercase">off</span>
                        ) : null}
                      </td>
                      <td className="py-2 pr-2 tabular-nums">
                        {row.currency || "—"}
                        {row.symbol ? ` ${row.symbol}` : ""}
                      </td>
                      <td className="py-2 pr-2 tabular-nums whitespace-nowrap">
                        {row.basic_price_label || "—"}
                      </td>
                      <td className="py-2 pr-2 tabular-nums whitespace-nowrap">
                        ≈{row.delivery_eta_minutes ?? status.markets_dashboard?.delivery_eta_minutes ?? 15}{" "}
                        мин
                      </td>
                      <td className="py-2 pr-2 tabular-nums">{row.daily_cap}</td>
                      <td className="py-2 pr-2 tabular-nums">{row.sent_today}</td>
                      <td className="py-2 pr-2 tabular-nums">{row.replies}</td>
                      <td className="py-2 pr-2 tabular-nums">{row.orders}</td>
                      <td className="py-2 tabular-nums">{row.phase}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {status?.adaptive_outreach ? (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold">Adaptive · outreach</h2>
            <p className="text-xs text-genesis-muted">
              {status.adaptive_outreach.note_ru ||
                "Меняет только лимиты и интервалы. Письма — только после одобрения."}
            </p>
            <div className="grid gap-2 text-sm sm:grid-cols-4">
              <p className="rounded-lg border border-genesis-border-subtle bg-black/20 px-3 py-2">
                <span className="text-genesis-muted">Здоровье</span>
                <span className="mt-1 block font-medium text-white">
                  {status.adaptive_outreach.current_health ?? "—"} ·{" "}
                  {status.adaptive_outreach.current_health_label || "—"}
                </span>
              </p>
              <p className="rounded-lg border border-genesis-border-subtle bg-black/20 px-3 py-2">
                <span className="text-genesis-muted">Масштаб</span>
                <span className="mt-1 block font-medium text-white">
                  {status.adaptive_outreach.scaling_status || "—"}
                </span>
              </p>
              <p className="rounded-lg border border-genesis-border-subtle bg-black/20 px-3 py-2">
                <span className="text-genesis-muted">След. обзор</span>
                <span className="mt-1 block font-medium text-white text-[11px]">
                  {status.adaptive_outreach.next_review_at
                    ? String(status.adaptive_outreach.next_review_at).slice(0, 16)
                    : "скоро"}
                </span>
              </p>
              <p className="rounded-lg border border-genesis-border-subtle bg-black/20 px-3 py-2">
                <span className="text-genesis-muted">Интервал</span>
                <span className="mt-1 block font-medium text-white">
                  ≥ {status.adaptive_outreach.interval_sec ?? "—"}с
                </span>
              </p>
            </div>
            {status.adaptive_outreach.countries?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[40rem] text-left text-xs">
                  <thead className="text-genesis-muted">
                    <tr className="border-b border-genesis-border-subtle">
                      <th className="py-2 pr-2">Страна</th>
                      <th className="py-2 pr-2">Здоровье</th>
                      <th className="py-2 pr-2">Мягкая доля</th>
                      <th className="py-2 pr-2">Рекоменд.</th>
                      <th className="py-2">Авто-решение</th>
                    </tr>
                  </thead>
                  <tbody>
                    {status.adaptive_outreach.countries.map((c) => (
                      <tr key={c.code} className="border-b border-white/5 text-white/90">
                        <td className="py-2 pr-2">
                          {c.flag} {c.name_ru}
                          {c.paused ? (
                            <span className="ml-1 text-[10px] text-rose-300">ПАУЗА</span>
                          ) : null}
                        </td>
                        <td className="py-2 pr-2">
                          {c.health?.score} · {c.health?.label}
                        </td>
                        <td className="py-2 pr-2 tabular-nums">{c.current_cap}</td>
                        <td className="py-2 pr-2 tabular-nums">{c.recommended_cap}</td>
                        <td className="py-2">{c.scaling_status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {status.adaptive_outreach.roi_table?.length ? (
              <div className="overflow-x-auto">
                <p className="mb-1 text-[11px] font-medium text-white/80">
                  ROI-панель · {status.adaptive_outreach.roi_note_ru || "расход = письма × cost proxy"}
                </p>
                <table className="w-full min-w-[32rem] text-left text-xs">
                  <thead className="text-genesis-muted">
                    <tr className="border-b border-genesis-border-subtle">
                      <th className="py-2 pr-2">Страна</th>
                      <th className="py-2 pr-2">Потрачено</th>
                      <th className="py-2 pr-2">Сделок</th>
                      <th className="py-2 pr-2">Выручка</th>
                      <th className="py-2">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {status.adaptive_outreach.roi_table.map((r) => (
                      <tr key={`roi-${r.code}`} className="border-b border-white/5 text-white/90">
                        <td className="py-2 pr-2">
                          {r.flag} {r.name_ru}
                        </td>
                        <td className="py-2 pr-2 tabular-nums">{r.spent_eur} €</td>
                        <td className="py-2 pr-2 tabular-nums">{r.orders}</td>
                        <td className="py-2 pr-2 tabular-nums">{r.revenue_eur} €</td>
                        <td className="py-2 tabular-nums">
                          {r.roi == null ? "—" : `${r.roi}x`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {status.adaptive_outreach.last_decisions?.length ? (
              <div className="space-y-1 text-[11px] text-genesis-muted">
                <p className="font-medium text-white/80">История (последний обзор)</p>
                {status.adaptive_outreach.last_decisions.map((d) => (
                  <p key={`${d.code}-${d.from_cap}-${d.to_cap}`}>
                    {d.code}: {d.from_cap} → {d.to_cap} · {d.decision}
                    {d.reason ? ` · ${d.reason}` : ""}
                    {d.applied ? " · applied" : ""}
                  </p>
                ))}
              </div>
            ) : null}
            {status.adaptive_outreach.graphs?.note_ru ? (
              <p className="text-[11px] text-genesis-muted">{status.adaptive_outreach.graphs.note_ru}</p>
            ) : null}
            {status.adaptive_outreach.graphs?.days?.length ? (
              <div className="grid gap-2 text-[11px] text-genesis-muted sm:grid-cols-2">
                <p>
                  Письма/день:{" "}
                  {(status.adaptive_outreach.graphs.daily_emails || []).slice(-7).join(", ") || "—"}
                </p>
                <p>
                  Ответы %:{" "}
                  {(status.adaptive_outreach.graphs.reply_rate || []).slice(-7).join(", ") || "—"}
                </p>
                <p>
                  Bounce %:{" "}
                  {(status.adaptive_outreach.graphs.bounce_rate || []).slice(-7).join(", ") || "—"}
                </p>
                <p>
                  Здоровье:{" "}
                  {(status.adaptive_outreach.graphs.health_score || []).slice(-7).join(", ") || "—"}
                </p>
                <p>
                  Заказы: {(status.adaptive_outreach.graphs.orders || []).slice(-7).join(", ") || "—"}
                </p>
                <p>
                  Выручка:{" "}
                  {(status.adaptive_outreach.graphs.revenue || []).slice(-7).join(", ") || "—"}
                </p>
              </div>
            ) : (
              <p className="text-[11px] text-genesis-muted">
                Graphs появятся после первых weekly review снимков.
              </p>
            )}
          </section>
        ) : null}

        {worklist && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Горячие лиды из чата (сегодня)</h2>
            <p className="mt-2 text-xs text-genesis-muted">
              Model 3 — посетитель пишет на /capture, система квалифицирует и кладёт сюда. Продаёте лид партнёру.
            </p>
            {inboundLeads.length ? (
              <ul className="mt-4 space-y-3">
                {inboundLeads.map((lead) => (
                  <li key={lead.id} className="rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-3 text-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-white">{lead.company_name}</p>
                      <span className="text-xs text-emerald-300">
                        {formatEur(lead.potential_value_eur)} · score {lead.score}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-genesis-muted">{lead.fit_reason}</p>
                    <p className="mt-1 text-xs text-genesis-muted">Контакт: {lead.contact || "—"}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-xs text-genesis-muted">
                Пока пусто. Лейте трафик на /capture?niche=autoservice (или laptop_repair, plumber).
              </p>
            )}
          </section>
        )}

        {worklist && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Сегодня · ручной поиск ({worklist.target_per_day}/день)</h2>
            <p className="mt-2 text-xs text-genesis-muted">{worklist.note}</p>
            <ul className="mt-4 space-y-3">
              {worklist.segments.map((s) => (
                <li key={s.id} className="rounded-xl border border-genesis-border-subtle p-3 text-sm">
                  <p className="font-medium">{s.label}</p>
                  <p className="text-xs text-genesis-muted mt-1">
                    Города: {s.cities.join(", ")}
                  </p>
                  <p className="text-xs text-genesis-muted">
                    Сигналы: {s.signals.join(" · ")}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="genesis-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Лиды Country Desk</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                При Пуске старые черновики скрываются в архив. Новые лиды появляются по тикам
                (страна → город → ниша → draft → auto-confirm).
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void rebuildAllQuotes()}
                disabled={Boolean(busy)}
                className="rounded-lg border border-amber-500/50 bg-amber-950/40 px-3 py-2 text-sm font-medium text-amber-100 hover:bg-amber-900/40 disabled:opacity-60"
              >
                {busy === "rebuild" ? "Пересобираем…" : "Пересобрать все квоты"}
              </button>
              <button
                type="button"
                onClick={() => void resetDeskAndWallet()}
                disabled={Boolean(busy)}
                className="rounded-lg border border-rose-500/40 bg-rose-950/30 px-3 py-2 text-sm font-medium text-rose-100 hover:bg-rose-900/40 disabled:opacity-60"
              >
                {busy === "reset-desk" ? "Обнуляем…" : "Обнулить цифры + кошелёк"}
              </button>
              <button
                type="button"
                onClick={() => void refreshLeads()}
                disabled={Boolean(busy)}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-60"
              >
                {busy === "refresh" ? "Обновляем…" : "Обновить лиды"}
              </button>
            </div>
          </div>
          {message && !busy ? (
            <p
              className={`mt-3 rounded-lg border px-3 py-2 text-xs ${
                actionOk === false
                  ? "border-rose-500/40 bg-rose-950/30 text-rose-100"
                  : actionOk === true
                    ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-100"
                    : "border-white/10 bg-black/20 text-genesis-muted"
              }`}
            >
              {message}
            </p>
          ) : null}
          {pipeline.length === 0 ? (
            <p className="mt-4 text-sm text-genesis-muted">
              Список пуст. Нажмите ▶ Пуск или «Обновить лиды» — страны по очереди (US→DE→GB…).
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {pipeline.map((lead) => {
                const canLearn =
                  lead.outreach_status === "sent" ||
                  lead.status === "contacted" ||
                  lead.crm_status === "contacted" ||
                  lead.status === "replied";
                const open = learnLeadId === lead.id;
                return (
                  <li
                    key={lead.id}
                    className="rounded-xl border border-genesis-border-subtle bg-black/20 px-3 py-3 text-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-white">{lead.company_name}</p>
                      <span className="text-[11px] text-emerald-300">
                        {lead.market ? `${lead.market} · ` : ""}
                        {lead.outreach_status || "none"}
                        {lead.win_probability_pct != null
                          ? ` · win ${lead.win_probability_pct}%`
                          : ""}
                        {lead.niche ? ` · ${lead.niche}` : ""}
                        {lead.hunt_city ? ` · ${lead.hunt_city}` : ""}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-genesis-muted">
                      {(lead.website_url || "без сайта").slice(0, 60)} · score {lead.score}
                      {lead.lead_priority != null ? ` · priority ${lead.lead_priority}` : ""}
                      {lead.recommended_package_id ? ` · ${lead.recommended_package_id}` : ""}
                      {lead.expected_value_eur != null
                        ? ` · EV ~${Math.round(Number(lead.expected_value_eur))}€`
                        : ""}
                      {lead.recommended_price_eur
                        ? ` · ${
                            lead.recommended_price_label ||
                            formatLocalizedMoney(
                              lead.recommended_price_eur,
                              lead.recommended_currency || "EUR",
                            )
                          }`
                        : ""}
                    </p>
                    {lead.last_market_lesson ? (
                      <p className="mt-1 text-[11px] text-amber-100/80">
                        Урок: {lead.last_market_lesson}
                      </p>
                    ) : null}
                    {canLearn ? (
                      <div className="mt-2">
                        <button
                          type="button"
                          className="rounded-lg border border-amber-500/40 px-2 py-1 text-[11px] text-amber-100"
                          onClick={() =>
                            setLearnLeadId(open ? "" : lead.id)
                          }
                        >
                          {open ? "Скрыть" : "Что мы узнали?"}
                        </button>
                        {open ? (
                          <div className="mt-2 space-y-2 rounded-lg border border-white/10 bg-black/30 p-2">
                            <select
                              value={outcomeEvent}
                              onChange={(e) => {
                                const v = e.target.value;
                                setOutcomeEvent(v);
                                if (v === "no_reply") setMarketReason("no_reply");
                                if (v === "won" || v === "qualified" || v === "replied") {
                                  setMarketReason("interested");
                                }
                                if (v === "lost") setMarketReason("not_relevant");
                              }}
                              className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1.5 text-xs text-white"
                            >
                              <option value="no_reply">Не ответил</option>
                              <option value="lost">Ответил: отказ</option>
                              <option value="replied">Ответил: диалог</option>
                              <option value="qualified">Попросил созвон</option>
                              <option value="won">Купил</option>
                            </select>
                            <label className="block text-[11px] text-genesis-muted">
                              Причина (каталог)
                              <select
                                value={marketReason}
                                onChange={(e) => setMarketReason(e.target.value)}
                                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1.5 text-xs text-white"
                              >
                                <option value="subject_weak">Тема письма</option>
                                <option value="offer_miss">Оффер</option>
                                <option value="price">Цена</option>
                                <option value="not_relevant">Неактуально</option>
                                <option value="has_vendor">Уже есть подрядчик</option>
                                <option value="no_budget">Нет бюджета</option>
                                <option value="no_reply">Не удалось связаться / нет ответа</option>
                                <option value="interested">Заинтересовались</option>
                                <option value="other">Другое</option>
                              </select>
                            </label>
                            <textarea
                              value={marketLesson}
                              onChange={(e) => setMarketLesson(e.target.value)}
                              rows={2}
                              placeholder={
                                marketReason === "other"
                                  ? "Обязательный комментарий для «Другое»"
                                  : "Комментарий CEO (коротко, по желанию)"
                              }
                              className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-2 py-1.5 text-xs text-white"
                            />
                            <button
                              type="button"
                              disabled={busy === lead.id}
                              onClick={() => void recordMarketOutcome(lead.id)}
                              className="rounded-lg bg-amber-600/90 px-3 py-1.5 text-[11px] font-medium text-white disabled:opacity-50"
                            >
                              Сохранить урок
                            </button>
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Сгенерировать черновики (Places → очередь)</h2>
          <p className="mt-2 text-xs text-genesis-muted">
            Автопоиск в фоне запрещён. Это ручной запуск CEO: найти лидов и подготовить черновики.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <label className="text-xs text-genesis-muted">
              Город
              <input
                value={genCity}
                onChange={(e) => setGenCity(e.target.value)}
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white"
              />
            </label>
            <label className="text-xs text-genesis-muted">
              Запрос
              <input
                value={genQuery}
                onChange={(e) => setGenQuery(e.target.value)}
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white"
              />
            </label>
            <label className="text-xs text-genesis-muted">
              Лимит
              <input
                type="number"
                min={1}
                max={50}
                value={genLimit}
                onChange={(e) => setGenLimit(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm text-white"
              />
            </label>
          </div>
          <label className="mt-4 flex items-center gap-2 text-xs text-genesis-muted">
            <input
              type="checkbox"
              checked={forceSkipCheck}
              onChange={(e) => setForceSkipCheck(e.target.checked)}
              className="rounded border-genesis-border"
            />
            Черновик даже если у компании уже есть сайт (CEO force)
          </label>
          <div className="mt-4">
            <button
              type="button"
              onClick={generateDrafts}
              disabled={busy === "generate"}
              className="rounded-lg bg-genesis-accent px-4 py-2 text-sm font-medium text-white shadow-glow hover:brightness-110 disabled:opacity-60"
            >
              {busy === "generate" ? "Генерируем…" : "Сгенерировать"}
            </button>
          </div>
        </section>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Очередь одобрения CEO</h2>
          {queue.length === 0 ? (
            <p className="mt-3 text-sm text-genesis-muted">
              Пусто. Добавьте лида в{" "}
              <Link href="/opportunities" className="text-violet-400 underline">
                журнал
              </Link>
              , укажите сайт и нажмите «Подготовить КП».
            </p>
          ) : (
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <ul className="space-y-2">
                {queue.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelected(item);
                        setSiteProblemOk(false);
                        setBenefitOk(false);
                        setWouldSendOk(false);
                        setLawfulConfirmed(false);
                      }}
                      className={`w-full rounded-xl border p-3 text-left text-sm transition ${
                        selected?.id === item.id
                          ? "border-emerald-500/50 bg-emerald-950/20"
                          : "border-genesis-border-subtle hover:bg-genesis-bg/40"
                      }`}
                    >
                      <p className="font-medium">{item.company_name}</p>
                      <p className="text-xs text-genesis-muted">
                        {item.recommended_price_label ||
                          formatLocalizedMoney(
                            item.recommended_price_eur,
                            item.recommended_currency || "EUR",
                          )}{" "}
                        · {item.issue_count} issues · score {item.score}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>

              {selected && (
                <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-4 space-y-3">
                  <div>
                    <p className="text-xs text-genesis-muted">Почему эта компания</p>
                    <p className="text-sm">{selected.fit_reason || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-genesis-muted">Цена (рекомендация)</p>
                    <p className="text-sm font-medium">
                      {selected.recommended_price_label ||
                        formatLocalizedMoney(
                          selected.recommended_price_eur,
                          selected.recommended_currency || "EUR",
                        )}{" "}
                      · {selected.pricing_rationale}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-genesis-muted">Наблюдения по сайту (сканер)</p>
                    {selected.site_issues && selected.site_issues.length > 0 ? (
                      <ul className="mt-1 space-y-0.5 text-xs text-emerald-100/80">
                        {selected.site_issues.map((issue) => (
                          <li key={issue}>• {issue}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-amber-200/90">
                        Нет конкретных issues — письмо скорее шаблон. Доработайте вручную.
                      </p>
                    )}
                  </div>
                  {selected.suggested_services && selected.suggested_services.length > 0 && (
                    <div>
                      <p className="text-xs text-genesis-muted">Подходящие услуги (каталог)</p>
                      <p className="mt-1 text-sm text-sky-100/90">
                        {selected.suggested_services.join(" · ")}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-genesis-muted">Тема</p>
                    <p className="text-sm">{selected.email_subject}</p>
                  </div>
                  <pre className="max-h-48 overflow-auto rounded-lg bg-black/30 p-3 text-xs whitespace-pre-wrap">
                    {selected.proposed_message}
                  </pre>
                  <div className="flex flex-wrap gap-2">
                    <div className="w-full space-y-2 rounded-xl border border-genesis-border-subtle bg-white/[0.02] p-3 text-xs text-genesis-muted">
                      <p className="font-medium text-white/90">CEO-чеклист · снайпер-одобрение</p>
                      <p className="opacity-80">
                        Path A = Neustart (новая Landing), не починка. CTA в письме ведёт на /order.
                        KPI партии: сигнал рынка (ответ или клик), не число писем. Авто-ZIP — после
                        первой оплаты. Юридические механизмы ≠ гарантия законности.
                      </p>
                      <label className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={siteProblemOk}
                          onChange={(e) => setSiteProblemOk(e.target.checked)}
                          className="mt-0.5"
                        />
                        <span>
                          Есть конкретная проблема именно этого сайта? (не общая фраза, а
                          наблюдение)
                        </span>
                      </label>
                      <label className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={benefitOk}
                          onChange={(e) => setBenefitOk(e.target.checked)}
                          className="mt-0.5"
                        />
                        <span>Есть понятная польза именно для этого бизнеса?</span>
                      </label>
                      <label className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={wouldSendOk}
                          onChange={(e) => setWouldSendOk(e.target.checked)}
                          className="mt-0.5"
                        />
                        <span>
                          Я сам отправил бы такое письмо, если бы был владельцем этой компании?
                        </span>
                      </label>
                      <label className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={lawfulConfirmed}
                          onChange={(e) => setLawfulConfirmed(e.target.checked)}
                          className="mt-0.5"
                        />
                        <span>Проверена ли законность контакта? (ответственность на мне)</span>
                      </label>
                      <span className="block opacity-80">
                        Основание (кратко):
                        <input
                          value={lawfulNote}
                          onChange={(e) => setLawfulNote(e.target.value)}
                          placeholder="например: ручной выбор CEO, релевантное предложение, единичный контакт"
                          className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-xs text-white"
                        />
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => approve(selected.id)}
                      disabled={
                        busy === selected.id ||
                        !siteProblemOk ||
                        !benefitOk ||
                        !wouldSendOk ||
                        !lawfulConfirmed
                      }
                      className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
                    >
                      Одобрить
                    </button>
                    <button
                      type="button"
                      onClick={() => copyDraft(selected)}
                      className="rounded-lg border border-genesis-border px-3 py-2 text-xs"
                    >
                      Копировать
                    </button>
                    <button
                      type="button"
                      onClick={() => markSent(selected.id)}
                      className="rounded-lg border border-genesis-border px-3 py-2 text-xs"
                    >
                      Отправил вручную
                    </button>
                    <button
                      type="button"
                      onClick={() => reject(selected.id)}
                      className="rounded-lg border border-red-500/40 px-3 py-2 text-xs text-red-300"
                    >
                      Отклонить
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
          {message && (
            <p
              className={`mt-3 text-xs ${
                actionOk === false ? "text-rose-300" : actionOk === true ? "text-emerald-300" : "text-genesis-muted"
              }`}
            >
              {message}
            </p>
          )}
        </section>

        {evidence && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Доказательства</h2>
            <p className="mt-1 text-xs text-genesis-muted">
              {evidence.milestone_ru ||
                "KPI: качественные персонализированные контакты → ≥1 осмысленный ответ (не объём писем)."}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-center text-sm">
              <Stat label="Контакты" value={String(evidence.contacted)} />
              <Stat label="Ответы ← цель" value={String(evidence.replied)} />
              <Stat label="Продажи" value={String(evidence.won)} />
              <Stat label="Ответы %" value={`${evidence.reply_rate_pct}%`} />
            </div>
            {evidence.learning ? (
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-center text-sm">
                <Stat label="Отправлено" value={String(evidence.learning.sent)} />
                <Stat
                  label="Уроков"
                  value={String(evidence.learning.lessons_logged)}
                />
                <Stat
                  label="Без урока"
                  value={String(evidence.learning.pending_lessons)}
                />
                <Stat
                  label="Обучение"
                  value={`${evidence.learning.completeness_pct}%`}
                />
              </div>
            ) : null}
            <ul className="mt-4 space-y-1 text-sm text-genesis-muted">
              {evidence.insights.map((line) => (
                <li key={line}>• {line}</li>
              ))}
            </ul>
            {evidence.reason_counts && evidence.reason_counts.length > 0 ? (
              <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
                <table className="w-full text-left text-xs">
                  <thead className="bg-black/30 text-genesis-muted">
                    <tr>
                      <th className="px-3 py-2 font-medium">Причина</th>
                      <th className="px-3 py-2 font-medium text-right">Кол-во</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidence.reason_counts.map((row) => (
                      <tr key={row.reason} className="border-t border-white/5">
                        <td className="px-3 py-2 text-white/90">{row.label_ru}</td>
                        <td className="px-3 py-2 text-right tabular-nums text-emerald-300">
                          {row.count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {evidence.recent_lessons && evidence.recent_lessons.length > 0 ? (
              <div className="mt-4 space-y-2">
                <p className="text-xs font-medium text-white/80">Последние уроки</p>
                <ul className="space-y-1.5 text-xs text-genesis-muted">
                  {evidence.recent_lessons.map((row, idx) => (
                    <li
                      key={`${row.at || idx}-${row.company || ""}`}
                      className="rounded-lg border border-white/10 bg-black/20 px-2 py-1.5"
                    >
                      <span className="text-emerald-300/90">{row.company || "—"}</span>
                      <span className="opacity-60">
                        {" "}
                        · {row.reason_label_ru || row.event}
                      </span>
                      {row.comment ? (
                        <p className="mt-0.5 text-white/85">{row.comment}</p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <p className="mt-3 text-[11px] text-genesis-muted">{evidence.note}</p>
          </section>
        )}
      </div>
    </main>
  );
}

function Badge({ children, ok }: { children: React.ReactNode; ok: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 ${
        ok ? "bg-emerald-500/20 text-emerald-300" : "bg-genesis-elevated text-genesis-muted"
      }`}
    >
      {children}
    </span>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-3">
      <p className="text-lg font-bold tabular-nums">{value}</p>
      <p className="text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
