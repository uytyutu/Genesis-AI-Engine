"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TabId = "library" | "trends" | "drafts" | "queue" | "earnings";

type FeaturesSnap = {
  tiktok_enabled: boolean;
  media_engine_enabled?: boolean;
  path_a_independent?: boolean;
  status_ru?: string;
  principle_ru?: string;
  module?: string;
  config_path?: string;
};

type FactoryDash = {
  tiktok_enabled: boolean;
  counts: { library: number; drafts: number; queue: number; approved: number };
  channels: { id: string; label: string; stage: string; launch_order: number; next_slot: boolean }[];
  capcut: { connected: boolean; status_ru: string };
  earnings: {
    balance_in_virtus: number;
    withdraw_via: string;
    note_ru: string;
  };
  trends: { connected: boolean; note_ru: string; items: unknown[] };
  reality?: Record<string, boolean>;
  reality_note_ru: string;
  capabilities?: {
    available: { id: string; label_ru: string; ok: boolean }[];
    unavailable: { id: string; label_ru: string; ok: boolean }[];
  };
};

type Draft = {
  id: string;
  status: string;
  source?: string;
  niche?: string;
  city?: string;
  scenario?: { hook_de?: string; body_beats_de?: string[]; cta_de?: string };
};

type LibItem = { id: string; title: string; niche?: string; status?: string; note_ru?: string };
type QueueItem = {
  id: string;
  channel: string;
  status: string;
  queue_state?: string;
  display_status?: string;
  block_reason_ru?: string;
  publish_blocked?: string;
  publish_note_ru?: string;
  hook_de?: string;
  source?: string;
};

const TABS: { id: TabId; label: string }[] = [
  { id: "library", label: "Библиотека" },
  { id: "trends", label: "Тренды" },
  { id: "drafts", label: "Черновики" },
  { id: "queue", label: "Очередь" },
  { id: "earnings", label: "Доход" },
];

export default function TikTokHorizonPage() {
  const [snap, setSnap] = useState<FeaturesSnap | null>(null);
  const [dash, setDash] = useState<FactoryDash | null>(null);
  const [tab, setTab] = useState<TabId>("drafts");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [library, setLibrary] = useState<LibItem[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [niche, setNiche] = useState("Handwerk");
  const [city, setCity] = useState("Köln");
  const [issues, setIssues] = useState("Kein HTTPS\nKein WhatsApp-Button");
  const [libTitle, setLibTitle] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [fRes, dRes] = await Promise.all([
        fetch(`${API}/api/owner/features`),
        fetch(`${API}/api/owner/video-factory`),
      ]);
      if (fRes.ok) setSnap(await fRes.json());
      if (dRes.ok) setDash(await dRes.json());
      const [dr, li, qu] = await Promise.all([
        fetch(`${API}/api/owner/video-factory/drafts`),
        fetch(`${API}/api/owner/video-factory/library`),
        fetch(`${API}/api/owner/video-factory/queue`),
      ]);
      if (dr.ok) setDrafts((await dr.json()).items ?? []);
      if (li.ok) setLibrary((await li.json()).items ?? []);
      if (qu.ok) setQueue((await qu.json()).items ?? []);
    } catch {
      setMessage("Backend недоступен — флаги не прочитаны.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const enabled = snap?.tiktok_enabled === true;

  async function activate() {
    const ok = window.confirm(
      "Активировать Video Factory (TikTok Horizon)?\n\n" +
        "v0: сценарии и очередь статусов. Без автопубликации и без CapCut.\n" +
        "Path A (Stripe / Country Desk) не затрагивается.\n\n" +
        "Продолжить?",
    );
    if (!ok) return;
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/owner/features/tiktok/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ceo_confirmed: true }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка активации");
        return;
      }
      setSnap(body);
      setMessage("Флаг tiktok_enabled=true. Автопубликация не запущена.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function deactivate() {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/features/tiktok/deactivate`, {
        method: "POST",
      });
      if (res.ok) {
        setSnap(await res.json());
        setMessage("Kill switch снова OFF — безопасно.");
        await refresh();
      }
    } finally {
      setBusy(false);
    }
  }

  async function createDraft() {
    if (!enabled) {
      setMessage("Сначала включите kill switch.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/owner/video-factory/drafts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          niche,
          city,
          pattern_issues: issues,
          source: "manual",
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Не удалось создать черновик");
        return;
      }
      setMessage(`Черновик создан: ${body.draft?.id}`);
      await refresh();
      setTab("drafts");
    } finally {
      setBusy(false);
    }
  }

  async function approveDraft(id: string) {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/video-factory/drafts/${id}/approve`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка утверждения");
        return;
      }
      setMessage(`Утверждён: ${id}`);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function enqueue(id: string) {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/video-factory/queue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_id: id, channel: "tiktok" }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка очереди");
        return;
      }
      setMessage(`В очереди TikTok (publish blocked): ${body.item?.id}`);
      await refresh();
      setTab("queue");
    } finally {
      setBusy(false);
    }
  }

  async function addLibrary() {
    if (!libTitle.trim()) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/video-factory/library`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: libTitle.trim(), niche, source: "manual" }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка библиотеки");
        return;
      }
      setLibTitle("");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function setChannelStage(channel: string, stage: string) {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/video-factory/channels/${channel}/stage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ошибка стадии канала");
        return;
      }
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="mx-auto max-w-4xl space-y-6 animate-fade-up px-4">
        <header className="rounded-2xl border border-white/10 bg-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.35em] text-amber-200/80">
            Horizon · Video Factory v0
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Video Factory</h1>
          <p className="mt-2 text-sm text-genesis-muted">
            Отдельная ниша заработка: сценарии → очередь каналов. Запуск по очереди (TikTok
            первый). Path A не зависит от этого модуля.
          </p>
          <p className="mt-3 text-xs text-amber-100/90">
            {dash?.reality_note_ru ||
              snap?.principle_ru ||
              "Ролик только из повторяющейся закономерности → человек → /order."}
          </p>
        </header>

        <section className="genesis-card space-y-3 p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Kill switch</h2>
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs ${
                enabled ? "bg-amber-500/20 text-amber-200" : "bg-emerald-500/20 text-emerald-300"
              }`}
            >
              {snap?.status_ru ?? "…"}
            </span>
          </div>
          <p className="text-xs text-genesis-muted">
            Модуль: <code className="text-white/80">{snap?.module ?? "modules/tiktok_factory"}</code>
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {!enabled ? (
              <button
                type="button"
                disabled={busy}
                onClick={() => void activate()}
                className="rounded-lg bg-amber-600/90 px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
              >
                Активировать направление
              </button>
            ) : (
              <button
                type="button"
                disabled={busy}
                onClick={() => void deactivate()}
                className="rounded-lg border border-emerald-500/40 px-4 py-2 text-sm text-emerald-200 disabled:opacity-50"
              >
                Выключить (kill switch)
              </button>
            )}
            <Link
              href="/acquisition"
              className="rounded-lg border border-genesis-border px-4 py-2 text-sm hover:bg-white/5"
            >
              ← Country Desk (Path A)
            </Link>
            <Link
              href="/ceo-site"
              className="rounded-lg border border-genesis-border px-4 py-2 text-sm hover:bg-white/5"
            >
              Сайт клиентов
            </Link>
          </div>
          {message ? <p className="text-xs text-genesis-muted">{message}</p> : null}
        </section>

        <section className="genesis-card space-y-3 p-5">
          <h2 className="text-sm font-semibold text-white">Capability Matrix</h2>
          <div className="grid gap-4 sm:grid-cols-2 text-sm">
            <ul className="space-y-1">
              {(dash?.capabilities?.available ?? []).map((c) => (
                <li key={c.id} className="text-emerald-300">
                  ✓ {c.label_ru}
                </li>
              ))}
            </ul>
            <ul className="space-y-1">
              {(dash?.capabilities?.unavailable ?? []).map((c) => (
                <li key={c.id} className="text-genesis-muted">
                  ✗ {c.label_ru}
                </li>
              ))}
            </ul>
          </div>
          {dash?.reality ? (
            <pre className="overflow-x-auto rounded-lg bg-black/30 p-3 text-[10px] text-emerald-100/70">
              {JSON.stringify(dash.reality, null, 2)}
            </pre>
          ) : null}
        </section>

        <section className="genesis-card space-y-3 p-5">
          <h2 className="text-sm font-semibold text-white">Каналы (по очереди)</h2>
          <ul className="space-y-2 text-sm">
            {(dash?.channels ?? []).map((ch) => (
              <li
                key={ch.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 px-3 py-2"
              >
                <span>
                  <span className="font-medium text-white">
                    {ch.launch_order}. {ch.label}
                  </span>
                  <span className="ml-2 text-xs text-genesis-muted">{ch.stage}</span>
                  {ch.next_slot ? (
                    <span className="ml-2 text-[10px] text-amber-200/80">следующий слот</span>
                  ) : null}
                </span>
                <span className="flex gap-1">
                  {(["dormant", "ready", "live"] as const).map((st) => (
                    <button
                      key={st}
                      type="button"
                      disabled={busy || !enabled}
                      onClick={() => void setChannelStage(ch.id, st)}
                      className={`rounded px-2 py-0.5 text-[10px] border ${
                        ch.stage === st
                          ? "border-amber-400/50 text-amber-100"
                          : "border-white/10 text-genesis-muted"
                      } disabled:opacity-40`}
                    >
                      {st}
                    </button>
                  ))}
                </span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-genesis-muted">
            CapCut: {dash?.capcut.status_ru ?? "не подключено"} · live в v0 всё равно без публикации
          </p>
        </section>

        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`rounded-full px-3 py-1.5 text-xs ${
                tab === t.id
                  ? "bg-genesis-accent/20 text-white"
                  : "border border-white/10 text-genesis-muted hover:text-white"
              }`}
            >
              {t.label}
              {t.id === "library" && dash ? ` (${dash.counts.library})` : ""}
              {t.id === "drafts" && dash ? ` (${dash.counts.drafts})` : ""}
              {t.id === "queue" && dash ? ` (${dash.counts.queue})` : ""}
            </button>
          ))}
        </div>

        {tab === "library" && (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold text-white">Библиотека</h2>
            <p className="text-xs text-genesis-muted">Метаданные сценариев/карточек — без MP4 в v0.</p>
            <div className="flex flex-wrap gap-2">
              <input
                value={libTitle}
                onChange={(e) => setLibTitle(e.target.value)}
                placeholder="Название карточки"
                className="min-w-[200px] flex-1 rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
                disabled={!enabled}
              />
              <button
                type="button"
                disabled={busy || !enabled}
                onClick={() => void addLibrary()}
                className="rounded-lg border border-genesis-border px-3 py-2 text-sm disabled:opacity-40"
              >
                Добавить
              </button>
            </div>
            <ul className="space-y-2 text-sm">
              {library.length === 0 ? (
                <li className="text-genesis-muted text-xs">Пусто — честное пустое состояние.</li>
              ) : (
                library.map((item) => (
                  <li key={item.id} className="rounded-lg border border-white/10 px-3 py-2">
                    <p className="font-medium text-white">{item.title}</p>
                    <p className="text-xs text-genesis-muted">
                      {item.status}
                      {item.niche ? ` · ${item.niche}` : ""}
                    </p>
                  </li>
                ))
              )}
            </ul>
          </section>
        )}

        {tab === "trends" && (
          <section className="genesis-card space-y-2 p-5">
            <h2 className="text-sm font-semibold text-white">Тренды</h2>
            {dash?.reality?.trend_analysis ? (
              <p className="text-sm text-genesis-muted">Анализ активен.</p>
            ) : (
              <p className="text-sm text-genesis-muted">
                {dash?.trends.note_ru ??
                  "Анализатор трендов не подключён — топ не имитируем."}
              </p>
            )}
          </section>
        )}

        {tab === "drafts" && (
          <section className="genesis-card space-y-4 p-5">
            <h2 className="text-sm font-semibold text-white">Черновики сценариев</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs text-genesis-muted">
                Ниша
                <input
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white"
                  disabled={!enabled}
                />
              </label>
              <label className="text-xs text-genesis-muted">
                Город
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white"
                  disabled={!enabled}
                />
              </label>
            </div>
            <label className="block text-xs text-genesis-muted">
              Повторяющиеся проблемы (по строке)
              <textarea
                value={issues}
                onChange={(e) => setIssues(e.target.value)}
                rows={3}
                className="mt-1 w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-white"
                disabled={!enabled}
              />
            </label>
            <button
              type="button"
              disabled={busy || !enabled}
              onClick={() => void createDraft()}
              className="rounded-lg bg-genesis-accent/90 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
            >
              Создать черновик
            </button>
            <ul className="space-y-3 text-sm">
              {drafts.length === 0 ? (
                <li className="text-xs text-genesis-muted">Нет черновиков.</li>
              ) : (
                drafts.map((d) => (
                  <li key={d.id} className="rounded-lg border border-white/10 px-3 py-3 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs text-genesis-muted">
                        {d.id} · {d.status} · source:{d.source || "manual"} · {d.niche}/{d.city}
                      </span>
                      <span className="flex gap-1">
                        <button
                          type="button"
                          disabled={busy || !enabled || d.status === "approved" || d.status === "queued"}
                          onClick={() => void approveDraft(d.id)}
                          className="rounded border border-emerald-500/30 px-2 py-0.5 text-[11px] text-emerald-200 disabled:opacity-40"
                        >
                          Утвердить
                        </button>
                        <button
                          type="button"
                          disabled={busy || !enabled}
                          onClick={() => void enqueue(d.id)}
                          className="rounded border border-amber-500/30 px-2 py-0.5 text-[11px] text-amber-100 disabled:opacity-40"
                        >
                          В очередь TikTok
                        </button>
                      </span>
                    </div>
                    {d.scenario?.hook_de ? (
                      <p className="text-white">{d.scenario.hook_de}</p>
                    ) : null}
                    {d.scenario?.body_beats_de?.length ? (
                      <ul className="text-xs text-genesis-muted space-y-1">
                        {d.scenario.body_beats_de.map((b) => (
                          <li key={b}>• {b}</li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </section>
        )}

        {tab === "queue" && (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold text-white">Очередь публикации</h2>
            <ul className="space-y-2 text-sm">
              {queue.length === 0 ? (
                <li className="text-xs text-genesis-muted">Очередь пуста.</li>
              ) : (
                queue.map((q) => (
                  <li key={q.id} className="rounded-lg border border-white/10 px-3 py-2 space-y-1">
                    <p className="font-medium text-white">{q.hook_de || q.id}</p>
                    <p className="text-xs">
                      <span className="text-genesis-muted">
                        {(q.queue_state || "queued").replace(/^./, (c) => c.toUpperCase())}
                      </span>
                      {" · "}
                      <span
                        className={
                          q.display_status === "Blocked" || q.status === "blocked"
                            ? "text-amber-200"
                            : "text-emerald-300"
                        }
                      >
                        {q.display_status || q.status}
                      </span>
                      <span className="text-genesis-muted"> · {q.channel}</span>
                    </p>
                    {q.block_reason_ru ? (
                      <p className="text-xs text-amber-100/90">
                        Причина: {q.block_reason_ru}
                      </p>
                    ) : null}
                    {q.publish_note_ru ? (
                      <p className="text-xs text-genesis-muted">{q.publish_note_ru}</p>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </section>
        )}

        {tab === "earnings" && (
          <section className="genesis-card space-y-3 p-5">
            <h2 className="text-sm font-semibold text-white">Доход</h2>
            {dash?.reality?.earn_money_inside_virtus ? (
              <p className="text-3xl font-bold tabular-nums">
                {dash?.earnings.balance_in_virtus ?? 0} €
              </p>
            ) : (
              <>
                <p className="text-3xl font-bold tabular-nums text-genesis-muted">0 €</p>
                <p className="text-xs text-amber-100/80">
                  earn_money_inside_virtus=false — баланс внутри Virtus не ведётся.
                </p>
              </>
            )}
            <p className="text-sm text-genesis-muted">
              {dash?.earnings.note_ru ??
                "Прибыль и вывод — в кабинете TikTok владельца. Virtus Core не кошелёк."}
            </p>
            <p className="text-xs text-genesis-muted">
              withdraw_via: {dash?.earnings.withdraw_via ?? "tiktok_owner_account"}
            </p>
          </section>
        )}
      </div>
    </main>
  );
}
