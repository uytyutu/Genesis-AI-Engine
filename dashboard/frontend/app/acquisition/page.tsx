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
  score: number;
};

type Evidence = {
  sample_size: number;
  contacted: number;
  replied: number;
  won: number;
  reply_rate_pct: number;
  insights: string[];
  evidence_ready: boolean;
  note: string;
};

type Worklist = {
  date: string;
  mode: string;
  note: string;
  target_per_day: number;
  segments: { id: string; label: string; cities: string[]; signals: string[] }[];
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

export default function AcquisitionPage() {
  const [status, setStatus] = useState<StudioStatus | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [inboundLeads, setInboundLeads] = useState<InboundLead[]>([]);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [worklist, setWorklist] = useState<Worklist | null>(null);
  const [selected, setSelected] = useState<QueueItem | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [lawfulConfirmed, setLawfulConfirmed] = useState(false);
  const [lawfulNote, setLawfulNote] = useState("");
  const [genCity, setGenCity] = useState("Pirna");
  const [genQuery, setGenQuery] = useState("Autowerkstatt");
  const [genLimit, setGenLimit] = useState(10);
  const [forceSkipCheck, setForceSkipCheck] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [st, q, ev, wl, inbox] = await Promise.all([
        fetch(`${API}/api/acquisition/status`),
        fetch(`${API}/api/acquisition/approval-queue`),
        fetch(`${API}/api/acquisition/evidence`),
        fetch(`${API}/api/acquisition/worklist`),
        fetch(`${API}/api/leads/inbox?today_only=true&limit=20`),
      ]);
      if (st.ok) setStatus(await st.json());
      if (q.ok) {
        const body = await q.json();
        const items = body.items ?? [];
        setQueue(items);
        setSelected((prev) => items.find((i: QueueItem) => i.id === prev?.id) ?? items[0] ?? null);
      }
      if (ev.ok) setEvidence(await ev.json());
      if (wl.ok) setWorklist(await wl.json());
      if (inbox.ok) {
        const body = await inbox.json();
        setInboundLeads(body.leads ?? []);
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
      if (!lawfulConfirmed) {
        setMessage("Перед Approve подтвердите законное основание контакта.");
        return;
      }
      const res = await fetch(`${API}/api/acquisition/opportunities/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: "lawful_basis", note: lawfulNote }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Одобрено" : "Ошибка"));
      refresh();
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
          <h1 className="mt-2 text-2xl font-semibold">Business Acquisition Studio</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Virtus Core готовит продажи. CEO подтверждает отправку. {status?.law}
          </p>
          {status && (
            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <Badge ok={!status.auto_send}>Без автоотправки</Badge>
              <Badge ok={!status.auto_search}>Без автопоиска</Badge>
              <Badge ok={status.outreach_send_enabled}>Resend при Approve</Badge>
              <span className="text-genesis-muted self-center">
                Очередь: {status.pending_approval_count} · Отправлено: {status.sent_count}
              </span>
            </div>
          )}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <Link
              href="/capture?niche=autoservice"
              className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-emerald-100 hover:bg-emerald-950/30"
            >
              Чат-ловушка (лиды)
            </Link>
            <Link
              href="/opportunities"
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40"
            >
              Журнал возможностей
            </Link>
            <Link
              href="/"
              className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40"
            >
              {BRAND_NAME}
            </Link>
          </div>
        </header>

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
                      onClick={() => setSelected(item)}
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
                    <p className="text-xs text-genesis-muted">Тема</p>
                    <p className="text-sm">{selected.email_subject}</p>
                  </div>
                  <pre className="max-h-48 overflow-auto rounded-lg bg-black/30 p-3 text-xs whitespace-pre-wrap">
                    {selected.proposed_message}
                  </pre>
                  <div className="flex flex-wrap gap-2">
                    <label className="flex w-full items-start gap-2 rounded-xl border border-genesis-border-subtle bg-white/[0.02] p-3 text-xs text-genesis-muted">
                      <input
                        type="checkbox"
                        checked={lawfulConfirmed}
                        onChange={(e) => setLawfulConfirmed(e.target.checked)}
                        className="mt-0.5"
                      />
                      <span>
                        I confirm I have a lawful basis to contact this business.
                        <span className="block mt-2 opacity-80">
                          Основание (кратко):
                          <input
                            value={lawfulNote}
                            onChange={(e) => setLawfulNote(e.target.value)}
                            placeholder="например: ручной выбор CEO, релевантное предложение, единичный контакт"
                            className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-xs text-white"
                          />
                        </span>
                      </span>
                    </label>
                    <button
                      type="button"
                      onClick={() => approve(selected.id)}
                      disabled={busy === selected.id}
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
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-center text-sm">
              <Stat label="Контакты" value={String(evidence.contacted)} />
              <Stat label="Ответы" value={String(evidence.replied)} />
              <Stat label="Продажи" value={String(evidence.won)} />
              <Stat label="Reply %" value={`${evidence.reply_rate_pct}%`} />
            </div>
            <ul className="mt-4 space-y-1 text-sm text-genesis-muted">
              {evidence.insights.map((line) => (
                <li key={line}>• {line}</li>
              ))}
            </ul>
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
