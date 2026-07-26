"use client";

/**
 * TikTok Horizon — Owner Internal module (Mission Control style).
 * Stage 1–2: connect accounts → trends → drafts → human review → queue.
 * No live video generation / publish until later stages.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TabId = "start" | "accounts" | "trends" | "review" | "queue";

type Dash = {
  tiktok_enabled?: boolean;
  stage?: number;
  pipeline_ru?: string;
  note_ru?: string;
  counts?: Record<string, number>;
  capabilities?: Record<string, boolean>;
  visibility?: {
    visibility?: string;
    owner_internal_only?: boolean;
    note_ru?: string;
  };
  accounts?: TikTokAccount[];
  oauth?: { data?: { oauth_client_ready?: boolean } };
};

type TikTokAccount = {
  id: string;
  open_id?: string;
  display_name?: string | null;
  username?: string | null;
  status?: string;
  connected_at?: string;
  last_sync_at?: string;
  label?: string;
  tokens?: {
    has_access_token?: boolean;
    has_refresh_token?: boolean;
    access_token_expires_at?: string;
  };
};

type Trend = {
  trend_id: string;
  topic_label: string;
  growth_score: number;
  hook_style?: string;
  editing_style?: string;
  average_duration?: number;
};

type Draft = {
  id: string;
  status: string;
  title?: string;
  style_variant?: string;
  human_edited?: boolean;
  quality?: Record<string, number | string[]>;
  quality_ready?: boolean;
  script?: {
    hook_seconds?: string;
    caption?: string;
    narrator_text?: string;
    hashtags?: string[];
  };
  prompt?: { prompt_text?: string; video_api_enabled?: boolean };
  publish_window?: {
    window_start_local?: string;
    window_end_local?: string;
    confidence?: number;
    confidence_label?: string;
    reasons?: string[];
  };
};

type QueueItem = {
  id: string;
  draft_id?: string;
  title?: string;
  status?: string;
  publish_note_ru?: string;
  publish_enabled?: boolean;
};

const TABS: { id: TabId; label: string }[] = [
  { id: "start", label: "Старт" },
  { id: "accounts", label: "Аккаунты" },
  { id: "trends", label: "Тренды" },
  { id: "review", label: "Review" },
  { id: "queue", label: "Очередь" },
];

export default function TikTokHorizonPage() {
  const [dash, setDash] = useState<Dash | null>(null);
  const [tab, setTab] = useState<TabId>("start");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [trends, setTrends] = useState<Trend[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [accounts, setAccounts] = useState<TikTokAccount[]>([]);
  const [oauthReady, setOauthReady] = useState(false);
  const [selectedId, setSelectedId] = useState<string>("");
  const [editHook, setEditHook] = useState("");
  const [editCaption, setEditCaption] = useState("");
  const [editNarrator, setEditNarrator] = useState("");

  const enabled = dash?.tiktok_enabled === true;
  const selected = drafts.find((d) => d.id === selectedId) || drafts[0];
  const connectedCount = useMemo(
    () => accounts.filter((a) => a.status === "connected").length,
    [accounts],
  );

  const refresh = useCallback(async () => {
    try {
      const [dRes, tRes, drRes, qRes, aRes] = await Promise.all([
        fetch(`${API}/api/owner/tiktok-horizon`),
        fetch(`${API}/api/owner/tiktok-horizon/trends`),
        fetch(`${API}/api/owner/tiktok-horizon/drafts`),
        fetch(`${API}/api/owner/tiktok-horizon/queue`),
        fetch(`${API}/api/owner/tiktok-horizon/accounts`),
      ]);
      if (dRes.ok) {
        const d = await dRes.json();
        setDash(d);
        if (Array.isArray(d.accounts)) setAccounts(d.accounts);
      }
      if (tRes.ok) setTrends((await tRes.json()).items ?? []);
      if (drRes.ok) {
        const items = (await drRes.json()).items ?? [];
        setDrafts(items);
        if (!selectedId && items[0]?.id) setSelectedId(items[0].id);
      }
      if (qRes.ok) setQueue((await qRes.json()).items ?? []);
      if (aRes.ok) {
        const a = await aRes.json();
        setAccounts(a.accounts ?? []);
        setOauthReady(Boolean(a.oauth_client_ready));
      }
    } catch {
      setMessage("Backend недоступен. Запустите стек через Genesis.exe.");
    }
  }, [selectedId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get("tab");
    if (
      tabParam === "accounts" ||
      tabParam === "trends" ||
      tabParam === "review" ||
      tabParam === "queue" ||
      tabParam === "start"
    ) {
      setTab(tabParam);
    }
    if (params.get("oauth") === "ok") {
      setMessage("TikTok-аккаунт подключён. Можно включать анализ.");
      setTab("accounts");
    }
    const err = params.get("oauth_error");
    if (err) {
      setMessage(`OAuth: ${err}`);
      setTab("accounts");
    }
  }, []);

  useEffect(() => {
    if (!selected) return;
    setEditHook(selected.script?.hook_seconds || "");
    setEditCaption(selected.script?.caption || "");
    setEditNarrator(selected.script?.narrator_text || "");
  }, [selected?.id]);

  async function activate() {
    const ok = window.confirm(
      "Активировать TikTok Horizon?\n\n" +
        "Тренды → черновики → Human Review → очередь.\n" +
        "Публикация и live video API пока выключены.\n\nПродолжить?",
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
      setMessage("Horizon включён. Дальше: подключите аккаунт → анализ → черновики.");
      await refresh();
      setTab(connectedCount ? "trends" : "accounts");
    } finally {
      setBusy(false);
    }
  }

  async function deactivate() {
    setBusy(true);
    try {
      await fetch(`${API}/api/owner/features/tiktok/deactivate`, { method: "POST" });
      setMessage("Kill switch OFF.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function seedAndAnalyze() {
    if (!enabled) {
      setMessage("Сначала включите модуль на вкладке Старт.");
      setTab("start");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const observations = [
        {
          topic_tokens: ["handwerk", "anruf", "landing"],
          duration_sec: 22,
          hook_style: "question",
          editing_style: "fast_cut",
          caption_style: "short_cta",
          hashtag_pattern: ["handwerk", "tipps"],
          engagement_proxy: 2.5,
        },
        {
          topic_tokens: ["handwerk", "whatsapp"],
          duration_sec: 26,
          hook_style: "question",
          editing_style: "fast_cut",
          caption_style: "short_cta",
          hashtag_pattern: ["handwerk"],
          engagement_proxy: 3.0,
        },
        {
          topic_tokens: ["seo", "local"],
          duration_sec: 34,
          hook_style: "myth",
          editing_style: "talking_head",
          caption_style: "story",
          hashtag_pattern: ["seo"],
          engagement_proxy: 1.4,
        },
      ];
      const res = await fetch(`${API}/api/owner/tiktok-horizon/observations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ observations }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Ingest failed");
        return;
      }
      setMessage(`Анализ: ${body.ingested} наблюдений → ${(body.trends || []).length} трендов`);
      setTab("trends");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function generateDrafts() {
    if (!enabled) {
      setMessage("Сначала включите модуль на вкладке Старт.");
      setTab("start");
      return;
    }
    if (trends.length === 0) {
      setMessage("Сначала запустите анализ трендов.");
      setTab("trends");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/drafts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 3, language: "ru" }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Generate failed");
        return;
      }
      const first = body.drafts?.[0]?.id;
      if (first) setSelectedId(first);
      setTab("review");
      setMessage(`Создано черновиков сценариев: ${(body.drafts || []).length}`);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function saveEdits() {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/drafts/${selected.id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          edits: {
            hook_seconds: editHook,
            caption: editCaption,
            narrator_text: editNarrator,
          },
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Edit failed");
        return;
      }
      setMessage("Human Review сохранён.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/drafts/${selected.id}/approve`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Approve failed");
        return;
      }
      setMessage("Утверждено. Можно поставить в очередь.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function enqueue() {
    if (!selected) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/queue`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_id: selected.id }),
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Queue failed");
        return;
      }
      setTab("queue");
      setMessage("В очереди. Live publish пока отключён (Stage 1–2).");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function disconnectAccount(id: string) {
    if (!window.confirm("Отключить этот TikTok-аккаунт?")) return;
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/accounts/${id}/disconnect`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Disconnect failed");
        return;
      }
      setMessage("Аккаунт отключён.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function syncAccount(id: string) {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/accounts/${id}/sync`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Sync failed");
        return;
      }
      setMessage("Синхронизация выполнена.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function connectSandbox() {
    setBusy(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/owner/tiktok-horizon/accounts/sandbox`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setMessage(typeof body.detail === "string" ? body.detail : "Sandbox failed");
        return;
      }
      setMessage(
        body.note_ru ||
          "Sandbox-аккаунт привязан. Включите Horizon и запустите анализ трендов.",
      );
      await refresh();
      setTab("start");
    } finally {
      setBusy(false);
    }
  }

  const quality = selected?.quality || {};
  const step1Done = oauthReady;
  const step2Done = connectedCount > 0;
  const step3Done = enabled;
  const step4Done = trends.length > 0;
  const step5Done = drafts.length > 0;

  return (
    <main className="min-h-screen bg-[#070a12] text-zinc-100">
      <div className="mx-auto max-w-5xl px-4 py-8 pb-24">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-cyan-300/80">
              Virtus Core · Owner Internal
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white">
              TikTok Horizon
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-zinc-400">
              Модуль программы: подключить аккаунт → включить → анализ трендов → сценарии
              топ-видео → Human Review. Stage {dash?.stage ?? 2}. Публикация и live video API
              пока выключены.
            </p>
          </div>
          <Link
            href="/mission-control"
            className="rounded-lg border border-white/15 px-3 py-2 text-sm text-zinc-300 hover:border-cyan-400/40 hover:text-white"
          >
            ← Mission Control
          </Link>
        </div>

        {message ? (
          <p className="mb-4 rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            {message}
          </p>
        ) : null}

        <nav className="mb-6 flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`rounded-lg px-3 py-2 text-sm ${
                tab === t.id
                  ? "bg-cyan-500 text-black font-semibold"
                  : "border border-white/10 text-zinc-300 hover:border-white/25"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {tab === "start" && (
          <section className="space-y-5">
            <div className="rounded-2xl border border-white/10 bg-[#0c111c] p-5">
              <h2 className="text-lg font-semibold text-white">Как работать</h2>
              <ol className="mt-4 space-y-3 text-sm text-zinc-300">
                <li className="flex gap-3">
                  <span className={step1Done ? "text-emerald-400" : "text-zinc-500"}>
                    {step1Done ? "✔" : "1."}
                  </span>
                  <span>
                    OAuth client в `.env` (`TIKTOK_CLIENT_KEY` + `TIKTOK_CLIENT_SECRET`) —{" "}
                    {oauthReady ? "готово" : "нужно настроить"}
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className={step2Done ? "text-emerald-400" : "text-zinc-500"}>
                    {step2Done ? "✔" : "2."}
                  </span>
                  <span>
                    Подключить хотя бы один TikTok-аккаунт (вкладка Аккаунты → Connect TikTok)
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className={step3Done ? "text-emerald-400" : "text-zinc-500"}>
                    {step3Done ? "✔" : "3."}
                  </span>
                  <span>Включить kill switch модуля</span>
                </li>
                <li className="flex gap-3">
                  <span className={step4Done ? "text-emerald-400" : "text-zinc-500"}>
                    {step4Done ? "✔" : "4."}
                  </span>
                  <span>Запустить анализ трендов</span>
                </li>
                <li className="flex gap-3">
                  <span className={step5Done ? "text-emerald-400" : "text-zinc-500"}>
                    {step5Done ? "✔" : "5."}
                  </span>
                  <span>Сгенерировать сценарии топ-видео → Review → очередь</span>
                </li>
              </ol>
            </div>

            <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-[#0c111c] p-5">
              <span
                className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                  enabled
                    ? "bg-emerald-500/20 text-emerald-200"
                    : "bg-rose-500/20 text-rose-200"
                }`}
              >
                Kill switch: {enabled ? "ON" : "OFF"}
              </span>
              {!enabled ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void activate()}
                  className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
                >
                  Включить Horizon
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void deactivate()}
                  className="rounded-lg border border-white/20 px-4 py-2 text-sm text-zinc-200"
                >
                  Выключить
                </button>
              )}
              <button
                type="button"
                onClick={() => setTab("accounts")}
                className="rounded-lg border border-cyan-400/40 px-4 py-2 text-sm text-cyan-100"
              >
                {connectedCount ? `Аккаунты (${connectedCount})` : "Подключить аккаунт →"}
              </button>
              <button
                type="button"
                disabled={busy || !enabled}
                onClick={() => void seedAndAnalyze()}
                className="rounded-lg border border-white/15 px-4 py-2 text-sm disabled:opacity-40"
              >
                Анализ трендов
              </button>
              <button
                type="button"
                disabled={busy || !enabled || trends.length === 0}
                onClick={() => void generateDrafts()}
                className="rounded-lg border border-white/15 px-4 py-2 text-sm disabled:opacity-40"
              >
                Генерация сценариев
              </button>
            </div>

            <p className="text-xs text-zinc-500">
              {dash?.pipeline_ru} {dash?.note_ru}
            </p>
          </section>
        )}

        {tab === "accounts" && (
          <section className="space-y-4">
            <div className="rounded-2xl border border-white/10 bg-[#0c111c] p-5">
              <h2 className="text-lg font-semibold text-white">Привязка TikTok</h2>
              <p className="mt-2 text-sm text-zinc-400">
                Официальный OAuth. Токены хранятся зашифрованно. Можно несколько аккаунтов.
                Публикация отключена до следующих Stage.
              </p>
              <p className="mt-3 text-sm">
                OAuth client:{" "}
                <span className={oauthReady ? "text-emerald-300" : "text-amber-300"}>
                  {oauthReady
                    ? "ready"
                    : "нужны TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET в .env.local"}
                </span>
              </p>
              <a
                href={`${API}/api/owner/tiktok-horizon/oauth/start`}
                className={`mt-4 inline-flex rounded-lg px-4 py-2.5 text-sm font-semibold ${
                  oauthReady
                    ? "bg-cyan-500 text-black"
                    : "pointer-events-none bg-zinc-700 text-zinc-400"
                }`}
              >
                + Connect TikTok
              </a>
              <button
                type="button"
                disabled={busy}
                onClick={() => void connectSandbox()}
                className="mt-3 ml-0 inline-flex rounded-lg border border-amber-400/40 px-4 py-2.5 text-sm text-amber-100 sm:ml-3"
              >
                Привязать sandbox (анализ без OAuth)
              </button>
              {!oauthReady ? (
                <p className="mt-3 text-xs text-amber-200/90">
                  Ключей TikTok Developer пока нет — начните с sandbox, чтобы сразу запустить
                  анализ и генерацию сценариев. Позже замените на реальный Connect TikTok
                  (`TIKTOK_CLIENT_KEY` + `TIKTOK_CLIENT_SECRET` в `.env.local`).
                </p>
              ) : (
                <p className="mt-3 text-xs text-zinc-500">
                  Sandbox можно использовать параллельно с реальным аккаунтом для тестов
                  пайплайна.
                </p>
              )}
            </div>

            {accounts.length === 0 ? (
              <p className="rounded-xl border border-dashed border-white/15 px-4 py-8 text-center text-sm text-zinc-500">
                Нет подключённых аккаунтов. Нажмите Connect TikTok выше.
              </p>
            ) : (
              <ul className="space-y-3">
                {accounts.map((a) => (
                  <li
                    key={a.id}
                    className="rounded-xl border border-white/10 bg-[#0c111c] p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-white">
                          {a.status === "connected" ? "✔ " : ""}
                          {a.label || a.username || a.display_name || a.id}
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {a.status} · @{a.username || "—"} · sync {a.last_sync_at || "—"}
                        </p>
                        <p className="mt-1 text-xs text-zinc-600">
                          tokens: access={String(a.tokens?.has_access_token)} refresh=
                          {String(a.tokens?.has_refresh_token)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {a.status === "connected" ? (
                          <>
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => void syncAccount(a.id)}
                              className="rounded-lg border border-white/15 px-3 py-1.5 text-xs"
                            >
                              Sync
                            </button>
                            <a
                              href={`${API}/api/owner/tiktok-horizon/oauth/start`}
                              className="rounded-lg border border-white/15 px-3 py-1.5 text-xs"
                            >
                              Reconnect
                            </a>
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => void disconnectAccount(a.id)}
                              className="rounded-lg border border-rose-400/30 px-3 py-1.5 text-xs text-rose-200"
                            >
                              Disconnect
                            </button>
                          </>
                        ) : (
                          <a
                            href={`${API}/api/owner/tiktok-horizon/oauth/start`}
                            className="rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-black"
                          >
                            Reconnect
                          </a>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {connectedCount > 0 ? (
              <button
                type="button"
                onClick={() => setTab("start")}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
              >
                Аккаунт есть → включить и анализировать
              </button>
            ) : null}
          </section>
        )}

        {tab === "trends" && (
          <section className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled={busy || !enabled}
                onClick={() => void seedAndAnalyze()}
                className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-black disabled:opacity-40"
              >
                Запустить анализ
              </button>
              <button
                type="button"
                disabled={busy || !enabled || trends.length === 0}
                onClick={() => void generateDrafts()}
                className="rounded-lg border border-white/15 px-4 py-2 text-sm disabled:opacity-40"
              >
                Сгенерировать сценарии
              </button>
            </div>
            {trends.length === 0 ? (
              <p className="text-sm text-zinc-500">
                База трендов пуста. Нажмите «Запустить анализ» (sample observations → trend
                scoring). Официальный TikTok research API — следующим Stage.
              </p>
            ) : (
              <ul className="space-y-3">
                {trends.map((t) => (
                  <li
                    key={t.trend_id}
                    className="rounded-xl border border-white/10 bg-[#0c111c] p-4"
                  >
                    <p className="font-medium text-white">{t.topic_label}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      growth {t.growth_score} · hook {t.hook_style} · edit {t.editing_style} · ~
                      {t.average_duration}s
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {tab === "review" && (
          <section className="space-y-4">
            {drafts.length === 0 ? (
              <p className="text-sm text-zinc-500">
                Нет черновиков. Сначала анализ трендов → генерация сценариев.
              </p>
            ) : (
              <>
                <label className="block text-sm text-zinc-400">
                  Черновик
                  <select
                    className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                    value={selected?.id || ""}
                    onChange={(e) => setSelectedId(e.target.value)}
                  >
                    {drafts.map((d) => (
                      <option key={d.id} value={d.id}>
                        [{d.status}] {d.title}
                      </option>
                    ))}
                  </select>
                </label>

                {selected ? (
                  <div className="space-y-4 rounded-2xl border border-white/10 bg-[#0c111c] p-5">
                    <p className="text-xs text-zinc-500">
                      Style: {selected.style_variant} · edited:{" "}
                      {selected.human_edited ? "yes" : "no"} · ready:{" "}
                      {selected.quality_ready ? "yes" : "review"}
                    </p>
                    <div className="grid gap-2 text-xs text-zinc-400 sm:grid-cols-2">
                      {(
                        [
                          "originality",
                          "structure_diversity",
                          "visual_diversity",
                          "hook_strength",
                          "caption_quality",
                          "publishing_readiness",
                        ] as const
                      ).map((k) => (
                        <div key={k}>
                          {k}: {String(quality[k] ?? "—")}
                        </div>
                      ))}
                    </div>
                    <label className="block text-sm text-zinc-400">
                      Hook (первые 3 сек)
                      <textarea
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={editHook}
                        onChange={(e) => setEditHook(e.target.value)}
                        rows={2}
                      />
                    </label>
                    <label className="block text-sm text-zinc-400">
                      Сценарий / диктор
                      <textarea
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={editNarrator}
                        onChange={(e) => setEditNarrator(e.target.value)}
                        rows={6}
                      />
                    </label>
                    <label className="block text-sm text-zinc-400">
                      Описание
                      <textarea
                        className="mt-1 w-full rounded-lg border border-white/15 bg-black/40 px-3 py-2 text-white"
                        value={editCaption}
                        onChange={(e) => setEditCaption(e.target.value)}
                        rows={2}
                      />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void saveEdits()}
                        className="rounded-lg border border-white/15 px-3 py-2 text-sm"
                      >
                        Сохранить
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void approve()}
                        className="rounded-lg bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void enqueue()}
                        className="rounded-lg bg-cyan-500 px-3 py-2 text-sm font-semibold text-black"
                      >
                        В очередь
                      </button>
                    </div>
                  </div>
                ) : null}
              </>
            )}
          </section>
        )}

        {tab === "queue" && (
          <section>
            {queue.length === 0 ? (
              <p className="text-sm text-zinc-500">Очередь пуста.</p>
            ) : (
              <ul className="space-y-3">
                {queue.map((q) => (
                  <li
                    key={q.id}
                    className="rounded-xl border border-white/10 bg-[#0c111c] p-4"
                  >
                    <p className="font-medium text-white">{q.title || q.id}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {q.status} · publish={String(q.publish_enabled)}
                    </p>
                    <p className="mt-1 text-xs text-zinc-600">{q.publish_note_ru}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
