"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

import { BRAND_NAME } from "../lib/publicBrand";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StudioStatus = {
  version: string;
  name: string;
  auto_search: boolean;
  auto_send: boolean;
  outreach_send_enabled: boolean;
  outreach_send_note: string;
  law: string;
  pending_approval_count: number;
  sent_count: number;
  pipeline_count: number;
  manual_review_count?: number;
  auto_draft_max_eur?: number;
  pilot_catalog?: {
    checkout_online: string[];
    pilot_quote: string[];
    horizon: string[];
    note?: string;
  };
};

type QueueItem = {
  id: string;
  company_name: string;
  contact: string;
  website_url: string;
  recommended_price_eur: number;
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
  quality_archive?: boolean;
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
      setMessage("Не удалось загрузить Studio. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

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
    setMessage("");
    try {
      const res = await fetch(`${API}/api/acquisition/refresh-leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city: genCity,
          query: genQuery,
          limit: genLimit,
          auto_confirm: true,
        }),
      });
      const body = await res.json();
      setMessage(res.ok ? body.message_ru || "Лиды обновлены" : body.detail || "Ошибка обновления");
      if (body.pipeline) setPipeline(body.pipeline);
      if (body.gate_funnel) setFunnel(body.gate_funnel);
      await refresh();
    } finally {
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
        <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">Mission 1.5</p>
          <h1 className="mt-2 text-2xl font-semibold">Country Desk · Германия</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Поиск и подготовка лидов (KFZ, Zahnarzt…). Labeling Farm отдельно на «Ферма».{" "}
            {status?.law}
          </p>
          {status && (
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <Badge ok={!status.auto_send}>Без автоотправки</Badge>
              <Badge ok>Auto-draft ≤{status.auto_draft_max_eur ?? 50}€</Badge>
              <Badge ok={(status.manual_review_count ?? 0) === 0}>
                Manual-review: {status.manual_review_count ?? 0}
              </Badge>
              <Badge ok={status.outreach_send_enabled}>Resend при Approve</Badge>
              <span className="text-genesis-muted self-center">
                Approve: {status.pending_approval_count} · Отправлено: {status.sent_count}
              </span>
            </div>
          )}
          {status?.pilot_catalog && (
            <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-genesis-muted">
              <p className="font-medium text-white/90">Каталог услуг (пилот)</p>
              <p className="mt-1">
                Checkout: {(status.pilot_catalog.checkout_online || []).join(", ")} · Anfrage:{" "}
                {(status.pilot_catalog.pilot_quote || []).slice(0, 6).join(", ")}
                {(status.pilot_catalog.pilot_quote || []).length > 6 ? "…" : ""}
              </p>
              <p className="mt-1">{status.pilot_catalog.note}</p>
              <Link href="/services" className="mt-2 inline-block text-emerald-300 hover:underline">
                Открыть /services →
              </Link>
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
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
              Labeling Farm
            </Link>
            <Link
              href="/journal"
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40"
            >
              Журнал
            </Link>
          </div>
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
                Старые лиды не удаляются (архив/история). Новые добавляются через Places → ingest.
                В Approve попадают только подготовленные черновики.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void refreshLeads()}
              disabled={busy === "refresh" || busy === "generate"}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-60"
            >
              {busy === "refresh" ? "Обновляем…" : "Обновить лиды"}
            </button>
          </div>
          {pipeline.length === 0 ? (
            <p className="mt-4 text-sm text-genesis-muted">
              Список пуст. Нажмите «Обновить лиды» (Köln · Kfz) — Places работает.
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
                        {lead.outreach_status || "none"}
                        {lead.win_probability_pct != null
                          ? ` · win ${lead.win_probability_pct}%`
                          : ""}
                        {lead.niche ? ` · ${lead.niche}` : ""}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-genesis-muted">
                      {(lead.website_url || "без сайта").slice(0, 60)} · score {lead.score}
                      {lead.recommended_price_eur
                        ? ` · ${formatEur(lead.recommended_price_eur)}`
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
          <h2 className="text-sm font-semibold">Generate drafts (Google Places → очередь)</h2>
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
              {busy === "generate" ? "Генерируем…" : "Generate drafts"}
            </button>
          </div>
        </section>

        <section className="genesis-card p-5">
          <h2 className="text-sm font-semibold">Очередь Approve CEO</h2>
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
                        {formatEur(item.recommended_price_eur)} · {item.issue_count} issues · score{" "}
                        {item.score}
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
                      {formatEur(selected.recommended_price_eur)} · {selected.pricing_rationale}
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
                      <p className="font-medium text-white/90">CEO-чеклист · Sniper Approve</p>
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
                      Approve
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
          {message && <p className="mt-3 text-xs text-genesis-muted">{message}</p>}
        </section>

        {evidence && (
          <section className="genesis-card p-5">
            <h2 className="text-sm font-semibold">Evidence</h2>
            <p className="mt-1 text-xs text-genesis-muted">
              {evidence.milestone_ru ||
                "KPI: качественные персонализированные контакты → ≥1 осмысленный ответ (не объём писем)."}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-center text-sm">
              <Stat label="Контакты" value={String(evidence.contacted)} />
              <Stat label="Ответы ← цель" value={String(evidence.replied)} />
              <Stat label="Продажи" value={String(evidence.won)} />
              <Stat label="Reply %" value={`${evidence.reply_rate_pct}%`} />
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
                  label="Learning Score"
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
