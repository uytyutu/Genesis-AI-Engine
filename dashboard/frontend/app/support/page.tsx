"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { BRAND_NAME } from "../lib/publicBrand";

/** CEO desk → local backend. CORS always allows :3000 (see main.py). */
const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type TabId =
  | "inbox"
  | "needs_reply"
  | "waiting"
  | "closed"
  | "templates"
  | "auto_rules"
  | "conversation";

type SupportMessage = {
  id: string;
  direction: string;
  from?: string;
  text?: string;
  subject?: string;
  created_at?: string;
  auto?: boolean;
  auto_replied?: boolean;
};

type SupportThread = {
  id: string;
  from: string;
  subject: string;
  status: string;
  updated_at?: string;
  messages?: SupportMessage[];
  last_fingerprint?: string;
  email_status?: string;
  do_not_email?: boolean;
};

type Template = {
  id: string;
  name: string;
  subject: string;
  body: string;
  source_fingerprint?: string;
};

type AutoRule = {
  id: string;
  fingerprint: string;
  template_id: string;
  enabled: boolean;
  label?: string;
  hit_count?: number;
};

type SupportStatus = {
  configured?: boolean;
  inbound_ready?: boolean;
  inbound_webhook_secret_set?: boolean;
  has_api_key?: boolean;
  has_from_address?: boolean;
  support_email?: string;
};

const TABS: { id: TabId; label: string }[] = [
  { id: "inbox", label: "Inbox" },
  { id: "needs_reply", label: "Needs Reply" },
  { id: "waiting", label: "Waiting" },
  { id: "closed", label: "Closed" },
  { id: "templates", label: "Templates" },
  { id: "auto_rules", label: "Auto Rules" },
  { id: "conversation", label: "Conversation" },
];

export default function SupportPage() {
  const [tab, setTab] = useState<TabId>("needs_reply");
  const [status, setStatus] = useState<SupportStatus | null>(null);
  const [threads, setThreads] = useState<SupportThread[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [rules, setRules] = useState<AutoRule[]>([]);
  const [reply, setReply] = useState("");
  const [saveTemplate, setSaveTemplate] = useState(true);
  const [createRule, setCreateRule] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  const selected = useMemo(
    () => threads.find((t) => t.id === selectedId) || null,
    [threads, selectedId],
  );

  const loadAll = useCallback(async () => {
    setError("");
    try {
      const statusFilter =
        tab === "inbox" || tab === "templates" || tab === "auto_rules" || tab === "conversation"
          ? ""
          : tab;
      const qs = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
      const [st, th, tpl, rl] = await Promise.all([
        fetch(`${API}/api/support/status`),
        fetch(`${API}/api/support/threads${qs}`),
        fetch(`${API}/api/support/templates`),
        fetch(`${API}/api/support/auto-rules`),
      ]);
      if (!st.ok || !th.ok) {
        setError(
          "API недоступен (нужен Genesis.exe → Запустить, backend :8000). " +
            `${st.status}/${th.status}`,
        );
        return;
      }
      setStatus(await st.json());
      const body = await th.json();
      setThreads(body.items || []);
      if (tpl.ok) {
        const tbody = await tpl.json();
        setTemplates(tbody.items || []);
      }
      if (rl.ok) {
        const rbody = await rl.json();
        setRules(rbody.items || []);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "load_failed";
      const offline =
        /failed to fetch|networkerror|load failed|econnrefused/i.test(msg);
      setError(
        offline
          ? "Нет связи с API (Failed to fetch). Backend не запущен на :8000 — в Genesis.exe нажмите «Запустить», дождитесь 🟢, затем «Обновить»."
          : msg,
      );
    }
  }, [tab]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  async function sendReply() {
    if (!selectedId || !reply.trim()) return;
    setBusy(true);
    setNote("");
    try {
      const res = await fetch(`${API}/api/support/threads/${selectedId}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: reply,
          save_as_template: saveTemplate,
          create_auto_rule: createRule && saveTemplate,
          template_name: `Reply · ${selected?.subject || ""}`.slice(0, 80),
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(body.detail || "reply_failed");
        return;
      }
      setReply("");
      setNote(
        body.ok
          ? body.rule_id
            ? "Отправлено · шаблон + Auto Rule сохранены"
            : "Отправлено"
          : "Ответ сохранён, но Resend не настроен / ошибка отправки",
      );
      await loadAll();
    } finally {
      setBusy(false);
    }
  }

  async function setThreadStatus(next: string) {
    if (!selectedId) return;
    setBusy(true);
    try {
      await fetch(`${API}/api/support/threads/${selectedId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      await loadAll();
    } finally {
      setBusy(false);
    }
  }

  async function toggleRule(id: string, enabled: boolean) {
    await fetch(`${API}/api/support/auto-rules/${id}/enabled`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    await loadAll();
  }

  async function deleteRule(id: string) {
    await fetch(`${API}/api/support/auto-rules/${id}`, { method: "DELETE" });
    await loadAll();
  }

  async function deleteThread(id: string) {
    if (!id) return;
    if (!window.confirm("Удалить это письмо из Inbox? Восстановить нельзя.")) return;
    setBusy(true);
    setNote("");
    setError("");
    try {
      const res = await fetch(`${API}/api/support/threads/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.detail || "delete_failed");
        return;
      }
      if (selectedId === id) setSelectedId(null);
      setNote("Письмо удалено");
      await loadAll();
    } finally {
      setBusy(false);
    }
  }

  async function unsubscribeThread(id: string) {
    if (!id) return;
    const thread = threads.find((t) => t.id === id) || selected;
    const rawFrom = thread?.from || "";
    const fromMessages = (thread?.messages || [])
      .map((m) => m.from || "")
      .find((v) => v.includes("@"));
    const emailMatch = `${rawFrom} ${fromMessages || ""}`.match(
      /[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}/i,
    );
    const fromAddr = (emailMatch?.[0] || rawFrom).trim();
    if (
      !window.confirm(
        "Отписать адрес от маркетинговых / outreach писем?\n\n" +
          (fromAddr ? `${fromAddr}\n\n` : "") +
          "Диалог сохранится в истории и закроется. Письмо не удаляется.",
      )
    ) {
      return;
    }
    setBusy(true);
    setNote("");
    setError("");
    try {
      const payload = JSON.stringify({ email: fromAddr, thread_id: id });
      const res = await fetch(`${API}/api/support/threads/${id}/unsubscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        // Fallback: block by email only (works when thread lives on Railway)
        if (fromAddr && fromAddr.includes("@")) {
          const res2 = await fetch(`${API}/api/support/do-not-email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: payload,
          });
          const body2 = await res2.json().catch(() => ({}));
          if (res2.ok) {
            setTab("closed");
            setNote(
              `Unsubscribed successfully · ${body2.email || fromAddr} · Do Not Send` +
                (body2.leads_suppressed ? ` · лидов: ${body2.leads_suppressed}` : ""),
            );
            await loadAll();
            return;
          }
          const detail = body2.detail || body.detail || "unsubscribe_failed";
          setError(
            typeof detail === "string"
              ? detail === "not_found" || detail === "Not Found"
                ? `Не удалось отписать (${fromAddr}). Перезапустите Genesis и повторите.`
                : detail
              : "unsubscribe_failed",
          );
          return;
        }
        setError(
          body.detail === "not_found" || body.detail === "Not Found"
            ? "Не найден адрес отправителя для отписки. Откройте письмо и повторите."
            : body.detail || "unsubscribe_failed",
        );
        return;
      }
      setTab("closed");
      setNote(
        `Unsubscribed successfully · ${body.contact?.email || body.email || fromAddr || "email"} · Do Not Send` +
          (body.leads_suppressed ? ` · лидов: ${body.leads_suppressed}` : ""),
      );
      await loadAll();
    } finally {
      setBusy(false);
    }
  }

  function openThread(id: string) {
    setSelectedId(id);
    setTab("conversation");
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-6 text-white">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-emerald-300/80">{BRAND_NAME}</p>
          <h1 className="text-2xl font-semibold">Support</h1>
          <p className="mt-1 text-sm text-white/60">
            Входящая почта · шаблоны · автоответ на идентичные вопросы
          </p>
        </div>
        <Link href="/acquisition" className="text-sm text-emerald-300 hover:underline">
          ← Country Desk
        </Link>
      </div>

      <div
        className={`mb-4 rounded-xl border px-3 py-2 text-xs ${
          status?.inbound_ready
            ? "border-emerald-500/30 bg-emerald-950/30 text-emerald-100"
            : "border-amber-500/30 bg-amber-950/20 text-amber-100"
        }`}
      >
        {status?.inbound_ready ? (
          <span>
            Inbound готов · {status.support_email || "hello@…"} · Resend key + webhook secret
          </span>
        ) : (
          <span>
            Inbound ещё не полностью настроен
            {!status?.has_api_key ? " · нет RESEND_API_KEY" : ""}
            {!status?.has_from_address ? " · нет GENESIS_EMAIL_FROM" : ""}
            {!status?.inbound_webhook_secret_set ? " · нет RESEND_INBOUND_WEBHOOK_SECRET" : ""}
            {!status?.inbound_ready
              ? " · если ключи уже в dashboard/backend/.env.local — нажмите «Обновить» или перезапустите Genesis.exe"
              : ""}
            .
          </span>
        )}
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-full px-3 py-1 text-xs ${
              tab === t.id
                ? "bg-emerald-500/25 text-emerald-100"
                : "bg-white/5 text-white/60 hover:bg-white/10"
            }`}
          >
            {t.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => void loadAll()}
          className="ml-auto rounded-full border border-white/15 px-3 py-1 text-xs text-white/70 hover:bg-white/5"
        >
          Обновить
        </button>
      </div>

      {error ? (
        <p className="mb-3 rounded-lg border border-rose-500/30 bg-rose-950/30 px-3 py-2 text-sm text-rose-100">
          {error}
        </p>
      ) : null}
      {note ? (
        <p className="mb-3 rounded-lg border border-emerald-500/30 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-100">
          {note}
        </p>
      ) : null}

      {(tab === "inbox" ||
        tab === "needs_reply" ||
        tab === "waiting" ||
        tab === "closed") && (
        <div className="grid gap-4 lg:grid-cols-5">
          <ul className="space-y-2 lg:col-span-2">
            {threads.length === 0 ? (
              <li className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-6 text-center text-sm text-white/50">
                Нет писем в этом фильтре
              </li>
            ) : (
              threads.map((th) => (
                <li key={th.id} className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => openThread(th.id)}
                    className={`min-w-0 flex-1 rounded-xl border px-3 py-2.5 text-left transition ${
                      selectedId === th.id
                        ? "border-emerald-400/40 bg-emerald-950/30"
                        : "border-white/10 bg-white/[0.03] hover:border-white/20"
                    }`}
                  >
                    <p className="truncate text-sm font-medium text-white">{th.subject}</p>
                    <p className="mt-0.5 truncate text-[11px] text-white/50">{th.from}</p>
                    <p className="mt-1 text-[10px] uppercase tracking-wide text-white/40">
                      {th.status}
                    </p>
                  </button>
                  <button
                    type="button"
                    title="Удалить"
                    disabled={busy}
                    onClick={(e) => {
                      e.stopPropagation();
                      void deleteThread(th.id);
                    }}
                    className="shrink-0 rounded-xl border border-rose-500/30 bg-rose-950/20 px-2 text-xs text-rose-100 hover:bg-rose-950/40 disabled:opacity-40"
                  >
                    ✕
                  </button>
                </li>
              ))
            )}
          </ul>
          <ConversationPanel
            thread={selected}
            reply={reply}
            setReply={setReply}
            saveTemplate={saveTemplate}
            setSaveTemplate={setSaveTemplate}
            createRule={createRule}
            setCreateRule={setCreateRule}
            busy={busy}
            onSend={() => void sendReply()}
            onStatus={(s) => void setThreadStatus(s)}
            onUnsubscribe={() => selectedId && void unsubscribeThread(selectedId)}
            onDelete={() => selectedId && void deleteThread(selectedId)}
          />
        </div>
      )}

      {tab === "conversation" && (
        <ConversationPanel
          thread={selected}
          reply={reply}
          setReply={setReply}
          saveTemplate={saveTemplate}
          setSaveTemplate={setSaveTemplate}
          createRule={createRule}
          setCreateRule={setCreateRule}
          busy={busy}
          onSend={() => void sendReply()}
          onStatus={(s) => void setThreadStatus(s)}
          onUnsubscribe={() => selectedId && void unsubscribeThread(selectedId)}
          onDelete={() => selectedId && void deleteThread(selectedId)}
          full
        />
      )}

      {tab === "templates" && (
        <ul className="space-y-2">
          {templates.length === 0 ? (
            <li className="text-sm text-white/50">
              Шаблонов пока нет — ответьте из Conversation с галочкой «Сохранить как шаблон».
            </li>
          ) : (
            templates.map((t) => (
              <li
                key={t.id}
                className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3"
              >
                <p className="text-sm font-medium text-white">{t.name}</p>
                <p className="mt-1 text-xs text-white/50">{t.subject}</p>
                <p className="mt-2 whitespace-pre-wrap text-xs text-white/70">{t.body}</p>
              </li>
            ))
          )}
        </ul>
      )}

      {tab === "auto_rules" && (
        <ul className="space-y-2">
          {rules.length === 0 ? (
            <li className="text-sm text-white/50">
              Правил нет — при ответе включите «Создать Auto Rule» (идентичный fingerprint → автоответ).
            </li>
          ) : (
            rules.map((r) => (
              <li
                key={r.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3"
              >
                <div>
                  <p className="text-sm text-white">{r.label || r.fingerprint.slice(0, 12)}</p>
                  <p className="text-[11px] text-white/45">
                    hits: {r.hit_count || 0} · tpl {r.template_id.slice(0, 8)}…
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="rounded-lg border border-white/15 px-2 py-1 text-xs"
                    onClick={() => void toggleRule(r.id, !r.enabled)}
                  >
                    {r.enabled ? "Выкл" : "Вкл"}
                  </button>
                  <button
                    type="button"
                    className="rounded-lg border border-rose-500/30 px-2 py-1 text-xs text-rose-200"
                    onClick={() => void deleteRule(r.id)}
                  >
                    Удалить
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
      )}
    </main>
  );
}

function ConversationPanel({
  thread,
  reply,
  setReply,
  saveTemplate,
  setSaveTemplate,
  createRule,
  setCreateRule,
  busy,
  onSend,
  onStatus,
  onUnsubscribe,
  onDelete,
  full,
}: {
  thread: SupportThread | null;
  reply: string;
  setReply: (v: string) => void;
  saveTemplate: boolean;
  setSaveTemplate: (v: boolean) => void;
  createRule: boolean;
  setCreateRule: (v: boolean) => void;
  busy: boolean;
  onSend: () => void;
  onStatus: (s: string) => void;
  onUnsubscribe: () => void;
  onDelete: () => void;
  full?: boolean;
}) {
  if (!thread) {
    return (
      <div
        className={`rounded-xl border border-white/10 bg-white/[0.03] px-4 py-10 text-center text-sm text-white/45 ${
          full ? "" : "lg:col-span-3"
        }`}
      >
        Выберите письмо слева
      </div>
    );
  }
  const alreadyUnsub =
    Boolean(thread.do_not_email) ||
    String(thread.email_status || "").toLowerCase() === "unsubscribed";
  return (
    <div
      className={`flex flex-col rounded-xl border border-white/10 bg-white/[0.03] ${
        full ? "min-h-[420px]" : "lg:col-span-3"
      }`}
    >
      <div className="border-b border-white/10 px-4 py-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-medium text-white">{thread.subject}</p>
            <p className="text-xs text-white/50">{thread.from}</p>
            {alreadyUnsub ? (
              <p className="mt-1 text-[11px] text-amber-200/90">📧 Email status: Unsubscribed</p>
            ) : null}
          </div>
          <div className="flex shrink-0 flex-wrap items-center justify-end gap-1.5">
            <button
              type="button"
              disabled={busy || alreadyUnsub}
              onClick={onUnsubscribe}
              className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-2.5 py-1 text-xs text-amber-50 hover:bg-amber-950/50 disabled:opacity-40"
              title="Do Not Email — сохранить историю, закрыть диалог"
            >
              {alreadyUnsub ? "Unsubscribed" : "Unsubscribe"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={onDelete}
              className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-1 text-xs text-white/55 hover:bg-white/10 disabled:opacity-40"
              title="Удаляет письмо навсегда — для отписки используйте Unsubscribe"
            >
              Удалить
            </button>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {(["needs_reply", "waiting", "closed"] as const).map((s) => (
            <button
              key={s}
              type="button"
              disabled={busy}
              onClick={() => onStatus(s)}
              className={`rounded-full px-2 py-0.5 text-[10px] ${
                thread.status === s
                  ? "bg-emerald-500/25 text-emerald-100"
                  : "bg-white/5 text-white/50"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      <div className="max-h-[320px] flex-1 space-y-2 overflow-y-auto px-4 py-3">
        {(thread.messages || []).map((m) => (
          <div
            key={m.id}
            className={`rounded-lg px-3 py-2 text-xs ${
              m.direction === "inbound"
                ? "bg-white/5 text-white/80"
                : "bg-emerald-950/40 text-emerald-50"
            }`}
          >
            <p className="text-[10px] uppercase text-white/40">
              {m.direction}
              {m.auto || m.auto_replied ? " · auto" : ""} · {m.created_at?.slice(0, 19)}
            </p>
            <p className="mt-1 whitespace-pre-wrap">{m.text}</p>
          </div>
        ))}
      </div>
      <div className="border-t border-white/10 px-4 py-3">
        <textarea
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          rows={4}
          placeholder="Ответ клиенту…"
          className="w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white"
        />
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-white/60">
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={saveTemplate}
              onChange={(e) => setSaveTemplate(e.target.checked)}
            />
            Сохранить как шаблон
          </label>
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={createRule}
              disabled={!saveTemplate}
              onChange={(e) => setCreateRule(e.target.checked)}
            />
            Создать Auto Rule (идентичные)
          </label>
          <button
            type="button"
            disabled={busy || !reply.trim()}
            onClick={onSend}
            className="ml-auto rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-40"
          >
            {busy ? "…" : "Отправить"}
          </button>
        </div>
      </div>
    </div>
  );
}
