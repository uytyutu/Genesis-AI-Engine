"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TabId = "overview" | "trends" | "review" | "queue";

type Dash = {
  tiktok_enabled?: boolean;
  stage?: number;
  pipeline_ru?: string;
  note_ru?: string;
  counts?: Record<string, number>;
  capabilities?: Record<string, boolean>;
  adapters?: Record<string, { provider?: string; stage1_disabled?: boolean }>;
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
  { id: "overview", label: "Обзор" },
  { id: "trends", label: "Тренды" },
  { id: "review", label: "Human Review" },
  { id: "queue", label: "Очередь" },
];

export default function TikTokHorizonPage() {
  const [dash, setDash] = useState<Dash | null>(null);
  const [tab, setTab] = useState<TabId>("overview");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [trends, setTrends] = useState<Trend[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [editHook, setEditHook] = useState("");
  const [editCaption, setEditCaption] = useState("");
  const [editNarrator, setEditNarrator] = useState("");

  const enabled = dash?.tiktok_enabled === true;
  const selected = drafts.find((d) => d.id === selectedId) || drafts[0];

  const refresh = useCallback(async () => {
    try {
      const [dRes, tRes, drRes, qRes] = await Promise.all([
        fetch(`${API}/api/owner/tiktok-horizon`),
        fetch(`${API}/api/owner/tiktok-horizon/trends`),
        fetch(`${API}/api/owner/tiktok-horizon/drafts`),
        fetch(`${API}/api/owner/tiktok-horizon/queue`),
      ]);
      if (dRes.ok) setDash(await dRes.json());
      if (tRes.ok) setTrends((await tRes.json()).items ?? []);
      if (drRes.ok) {
        const items = (await drRes.json()).items ?? [];
        setDrafts(items);
        if (!selectedId && items[0]?.id) setSelectedId(items[0].id);
      }
      if (qRes.ok) setQueue((await qRes.json()).items ?? []);
    } catch {
      setMessage("Backend недоступен.");
    }
  }, [selectedId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!selected) return;
    setEditHook(selected.script?.hook_seconds || "");
    setEditCaption(selected.script?.caption || "");
    setEditNarrator(selected.script?.narrator_text || "");
  }, [selected?.id]);

  async function activate() {
    const ok = window.confirm(
      "Активировать TikTok Horizon Stage 1?\n\n" +
        "Тренды → черновики → Human Review → очередь.\n" +
        "Без генерации видео и без публикации.\n\nПродолжить?",
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
      setMessage("Horizon включён (kill switch ON). Публикация не запущена.");
      await refresh();
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
      setMessage("Сначала включите kill switch.");
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
      setMessage(`Observations: ${body.ingested}. Trends: ${(body.trends || []).length}`);
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function generateDrafts() {
    if (!enabled) {
      setMessage("Сначала включите kill switch.");
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
      setMessage(`Создано черновиков: ${(body.drafts || []).length}`);
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
      setMessage("В очереди. Публикация Stage 1 отключена.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  const quality = selected?.quality || {};

  return (
    <main
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "2rem 1.25rem 4rem",
        fontFamily: "Georgia, 'Times New Roman', serif",
        color: "#1a1a1a",
        background:
          "linear-gradient(165deg, #f7f3eb 0%, #ebe4d8 45%, #e2ddd4 100%)",
        minHeight: "100vh",
      }}
    >
      <p style={{ margin: 0, fontSize: 13, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        Virtus Core · Internal
      </p>
      <h1 style={{ margin: "0.35rem 0 0.5rem", fontSize: "2rem", fontWeight: 600 }}>
        TikTok Horizon
      </h1>
      <p style={{ margin: "0 0 1rem", maxWidth: 52, fontSize: 15, lineHeight: 1.45 }}>
        Stage 1 Foundation — тренды, идеи, сценарии, промпты, качество, Human Review, очередь.
        Без генерации видео и без публикации.
      </p>
      <p style={{ margin: "0 0 1.5rem" }}>
        <Link href="/mission-control">← Mission Control</Link>
      </p>

      <section
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          alignItems: "center",
          marginBottom: "1.25rem",
        }}
      >
        <span
          style={{
            padding: "0.35rem 0.7rem",
            border: "1px solid #222",
            background: enabled ? "#d8f0d0" : "#f0d8d8",
          }}
        >
          Kill switch: {enabled ? "ON" : "OFF"}
        </span>
        {!enabled ? (
          <button type="button" disabled={busy} onClick={() => void activate()}>
            Активировать Horizon
          </button>
        ) : (
          <button type="button" disabled={busy} onClick={() => void deactivate()}>
            Выключить
          </button>
        )}
        <button type="button" disabled={busy || !enabled} onClick={() => void seedAndAnalyze()}>
          Ingest sample trends
        </button>
        <button type="button" disabled={busy || !enabled} onClick={() => void generateDrafts()}>
          Generate drafts
        </button>
      </section>

      {message ? (
        <p style={{ marginBottom: "1rem", padding: "0.75rem", background: "#fff8e8", border: "1px solid #c9b48a" }}>
          {message}
        </p>
      ) : null}

      <nav style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            style={{
              padding: "0.4rem 0.8rem",
              border: "1px solid #333",
              background: tab === t.id ? "#222" : "transparent",
              color: tab === t.id ? "#f5f0e6" : "#222",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <section>
          <p>{dash?.pipeline_ru}</p>
          <p style={{ opacity: 0.85 }}>{dash?.note_ru}</p>
          <ul>
            {Object.entries(dash?.counts || {}).map(([k, v]) => (
              <li key={k}>
                {k}: {v}
              </li>
            ))}
          </ul>
          <h3>Capabilities</h3>
          <ul>
            {Object.entries(dash?.capabilities || {}).map(([k, v]) => (
              <li key={k}>
                {v ? "✓" : "✗"} {k}
              </li>
            ))}
          </ul>
        </section>
      )}

      {tab === "trends" && (
        <section>
          {trends.length === 0 ? (
            <p>База трендов пуста. Сначала Ingest sample trends (или официальный API позже).</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {trends.map((t) => (
                <li
                  key={t.trend_id}
                  style={{
                    marginBottom: "0.75rem",
                    padding: "0.85rem",
                    background: "rgba(255,255,255,0.55)",
                    border: "1px solid #cfc4b0",
                  }}
                >
                  <strong>{t.topic_label}</strong>
                  <div style={{ fontSize: 14, marginTop: 4 }}>
                    growth {t.growth_score} · hook {t.hook_style} · edit {t.editing_style} · ~
                    {t.average_duration}s
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "review" && (
        <section>
          {drafts.length === 0 ? (
            <p>Нет черновиков — Generate drafts после анализа трендов.</p>
          ) : (
            <>
              <label style={{ display: "block", marginBottom: 12 }}>
                Черновик{" "}
                <select
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

              {selected && (
                <>
                  <p style={{ fontSize: 14 }}>
                    Style: {selected.style_variant} · Human edited:{" "}
                    {selected.human_edited ? "yes" : "no"} · Ready:{" "}
                    {selected.quality_ready ? "yes" : "review more"}
                  </p>

                  <h3>Content Quality</h3>
                  <ul>
                    {(["originality", "structure_diversity", "visual_diversity", "hook_strength", "caption_quality", "publishing_readiness"] as const).map(
                      (k) => (
                        <li key={k}>
                          {k}: {String(quality[k] ?? "—")}
                        </li>
                      ),
                    )}
                  </ul>

                  <h3>Publish window (confidence ≠ virality)</h3>
                  <p style={{ fontSize: 14 }}>
                    {selected.publish_window?.window_start_local} →{" "}
                    {selected.publish_window?.window_end_local}
                    <br />
                    Confidence: {selected.publish_window?.confidence_label} (
                    {selected.publish_window?.confidence})
                  </p>
                  <ul>
                    {(selected.publish_window?.reasons || []).map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>

                  <h3>Human Review checklist</h3>
                  <label style={{ display: "block", marginBottom: 8 }}>
                    Hook (первые 3 сек)
                    <textarea
                      value={editHook}
                      onChange={(e) => setEditHook(e.target.value)}
                      rows={2}
                      style={{ width: "100%", display: "block", marginTop: 4 }}
                    />
                  </label>
                  <label style={{ display: "block", marginBottom: 8 }}>
                    Сценарий / диктор
                    <textarea
                      value={editNarrator}
                      onChange={(e) => setEditNarrator(e.target.value)}
                      rows={6}
                      style={{ width: "100%", display: "block", marginTop: 4 }}
                    />
                  </label>
                  <label style={{ display: "block", marginBottom: 12 }}>
                    Описание
                    <textarea
                      value={editCaption}
                      onChange={(e) => setEditCaption(e.target.value)}
                      rows={2}
                      style={{ width: "100%", display: "block", marginTop: 4 }}
                    />
                  </label>

                  <details style={{ marginBottom: 12 }}>
                    <summary>Prompt для будущего Video API (не вызывается)</summary>
                    <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>
                      {selected.prompt?.prompt_text}
                    </pre>
                  </details>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button type="button" disabled={busy} onClick={() => void saveEdits()}>
                      Сохранить правки
                    </button>
                    <button type="button" disabled={busy} onClick={() => void approve()}>
                      Approve
                    </button>
                    <button type="button" disabled={busy} onClick={() => void enqueue()}>
                      В очередь
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </section>
      )}

      {tab === "queue" && (
        <section>
          {queue.length === 0 ? (
            <p>Очередь пуста.</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {queue.map((q) => (
                <li
                  key={q.id}
                  style={{
                    marginBottom: "0.75rem",
                    padding: "0.85rem",
                    background: "rgba(255,255,255,0.55)",
                    border: "1px solid #cfc4b0",
                  }}
                >
                  <strong>{q.title || q.id}</strong>
                  <div style={{ fontSize: 14 }}>
                    {q.status} · publish={String(q.publish_enabled)}
                    <br />
                    {q.publish_note_ru}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}
