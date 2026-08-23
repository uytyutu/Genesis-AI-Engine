"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";
import { workspaceCopy, workspaceUiLang, type WorkspaceUiLang } from "../../lib/workspaceCopy";
import { useLocale } from "../../context/LocaleContext";

const API = publicApiBase();
const POLL_MS = 8000;

type Thread = {
  thread_id: string;
  channel: string;
  bot_id: string;
  bot_name?: string;
  customer_name: string;
  preview: string;
  updated_at: string;
  unread_count: number;
  status?: string;
  handling?: string;
  send_supported?: boolean;
};

type Message = {
  id: string;
  direction: "INBOUND" | "OUTBOUND" | string;
  text: string;
  channel: string;
  timestamp?: string;
};

type InboxCopy = {
  title: string;
  subtitle: string;
  search: string;
  all: string;
  unread: string;
  telegram: string;
  website: string;
  send: string;
  retry: string;
  empty: string;
  noMessages: string;
  loadError: string;
  sendError: string;
  sending: string;
  back: string;
  open: string;
  aiReady: string;
  human: string;
  login: string;
  unsupported: string;
  placeholder: string;
};

const COPY: Record<WorkspaceUiLang, InboxCopy> = {
  de: {
    title: "Posteingang",
    subtitle: "Telegram und Website-Chat an einem Ort.",
    search: "Suchen…",
    all: "Alle",
    unread: "Ungelesen",
    telegram: "Telegram",
    website: "Website",
    send: "Senden",
    retry: "Erneut",
    empty: "Keine Nachrichten",
    noMessages: "Noch keine Nachrichten in diesem Gespräch.",
    loadError: "Nachrichten konnten nicht geladen werden.",
    sendError: "Nachricht konnte nicht gesendet werden.",
    sending: "Senden…",
    back: "← Gespräche",
    open: "Öffnen",
    aiReady: "AI-ready",
    human: "Human",
    login: "Bitte im Workspace anmelden.",
    unsupported: "Antwort über diesen Kanal ist noch nicht möglich (Visitor-initiiert).",
    placeholder: "Nachricht schreiben…",
  },
  en: {
    title: "Inbox",
    subtitle: "Telegram and Website Chat in one place.",
    search: "Search…",
    all: "All",
    unread: "Unread",
    telegram: "Telegram",
    website: "Website",
    send: "Send",
    retry: "Retry",
    empty: "No conversations",
    noMessages: "No messages in this conversation yet.",
    loadError: "Could not load messages.",
    sendError: "Message could not be sent.",
    sending: "Sending…",
    back: "← Conversations",
    open: "Open",
    aiReady: "AI-ready",
    human: "Human",
    login: "Please sign in to Workspace.",
    unsupported: "Reply on this channel is not available yet (visitor-initiated).",
    placeholder: "Write a message…",
  },
  ru: {
    title: "Входящие",
    subtitle: "Telegram и Website Chat в одном месте.",
    search: "Поиск…",
    all: "Все",
    unread: "Непрочитанные",
    telegram: "Telegram",
    website: "Website",
    send: "Отправить",
    retry: "Ещё раз",
    empty: "Нет сообщений",
    noMessages: "В этом диалоге пока нет сообщений.",
    loadError: "Не удалось загрузить сообщения.",
    sendError: "Не удалось отправить сообщение.",
    sending: "Отправка…",
    back: "← Диалоги",
    open: "Открыть",
    aiReady: "AI-ready",
    human: "Human",
    login: "Войдите в Workspace.",
    unsupported: "Ответ в этом канале пока недоступен (инициирует посетитель).",
    placeholder: "Напишите сообщение…",
  },
};

function channelLabel(ch: string, t: InboxCopy): string {
  if (ch === "telegram") return `Telegram · ${t.telegram}`;
  if (ch === "webchat") return `Website · ${t.website}`;
  return ch;
}

function channelBadge(ch: string): string {
  if (ch === "telegram") return "Telegram";
  if (ch === "webchat") return "Website";
  return ch;
}

function ClientInboxPage() {
  const { uiLocale } = useLocale();
  const lang = workspaceUiLang(uiLocale);
  const t = COPY[lang] || COPY.de;
  const navCopy = workspaceCopy(lang);

  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "unread" | "telegram" | "website">("all");
  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [thread, setThread] = useState<Thread | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [composer, setComposer] = useState("");
  const [sendState, setSendState] = useState<"idle" | "sending" | "failed">("idle");
  const [sendError, setSendError] = useState<string | null>(null);

  const queryParams = useMemo(() => {
    const p = new URLSearchParams();
    if (filter === "unread") p.set("unread", "1");
    if (filter === "telegram") p.set("channel", "telegram");
    if (filter === "website") p.set("channel", "website");
    if (q.trim()) p.set("q", q.trim());
    p.set("limit", "50");
    return p.toString();
  }, [filter, q]);

  const loadThreads = useCallback(async () => {
    if (!getClientToken()) {
      setError(t.login);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API}/api/client/inbox/threads?${queryParams}`, {
        headers: clientAuthHeaders(),
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(formatApiDetail(body) || t.loadError);
        return;
      }
      setError(null);
      setThreads(Array.isArray(body.threads) ? body.threads : []);
    } catch {
      setError(t.loadError);
    } finally {
      setLoading(false);
    }
  }, [queryParams, t.loadError, t.login]);

  const openThread = useCallback(
    async (threadId: string) => {
      setSelectedId(threadId);
      setDetailLoading(true);
      setSendState("idle");
      setSendError(null);
      try {
        const res = await fetch(
          `${API}/api/client/inbox/threads/${encodeURIComponent(threadId)}`,
          { headers: clientAuthHeaders(), cache: "no-store" },
        );
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setSendError(formatApiDetail(body) || t.loadError);
          return;
        }
        setThread(body.thread || null);
        setMessages(Array.isArray(body.messages) ? body.messages : []);
        await fetch(`${API}/api/client/inbox/threads/${encodeURIComponent(threadId)}/read`, {
          method: "POST",
          headers: clientAuthHeaders(),
        }).catch(() => undefined);
        void loadThreads();
      } catch {
        setSendError(t.loadError);
      } finally {
        setDetailLoading(false);
      }
    },
    [loadThreads, t.loadError],
  );

  const sendMessage = useCallback(async () => {
    if (!selectedId || !composer.trim()) return;
    setSendState("sending");
    setSendError(null);
    const text = composer.trim();
    try {
      const res = await fetch(
        `${API}/api/client/inbox/threads/${encodeURIComponent(selectedId)}/messages`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setSendState("failed");
        const reason = String(body?.detail || "");
        setSendError(reason === "CHANNEL_SEND_UNSUPPORTED" ? t.unsupported : formatApiDetail(body) || t.sendError);
        return;
      }
      setComposer("");
      setSendState("idle");
      setMessages(Array.isArray(body.messages) ? body.messages : messages);
      void loadThreads();
    } catch {
      setSendState("failed");
      setSendError(t.sendError);
    }
  }, [composer, loadThreads, messages, selectedId, t.sendError, t.unsupported]);

  useEffect(() => {
    void loadThreads();
    const id = window.setInterval(() => void loadThreads(), POLL_MS);
    return () => window.clearInterval(id);
  }, [loadThreads]);

  const showList = !selectedId;
  const showDetail = Boolean(selectedId);

  return (
    <ClientWorkspaceShell title={navCopy.nav.inbox || t.title} subtitle={t.subtitle}>
      <div className="flex flex-col gap-3 md:grid md:grid-cols-[minmax(240px,320px)_1fr] md:gap-4 md:min-h-[70vh]">
        {/* List */}
        <section
          className={`rounded-2xl border border-white/10 bg-white/[0.03] ${showDetail ? "hidden md:block" : "block"}`}
        >
          <div className="border-b border-white/10 p-3 space-y-2">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t.search}
              className="w-full rounded-xl border border-white/15 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-zinc-500"
            />
            <div className="flex flex-wrap gap-1.5">
              {(
                [
                  ["all", t.all],
                  ["unread", t.unread],
                  ["telegram", t.telegram],
                  ["website", t.website],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setFilter(id)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium ${
                    filter === id
                      ? "bg-emerald-500 text-black"
                      : "border border-white/15 text-zinc-300 hover:bg-white/5"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="max-h-[70vh] overflow-y-auto">
            {loading ? (
              <p className="p-4 text-sm text-zinc-500">…</p>
            ) : error ? (
              <div className="space-y-2 p-4">
                <p className="text-sm text-rose-300">{error}</p>
                <button
                  type="button"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs"
                  onClick={() => void loadThreads()}
                >
                  {t.retry}
                </button>
              </div>
            ) : threads.length === 0 ? (
              <p className="p-4 text-sm text-zinc-500">{t.empty}</p>
            ) : (
              <ul className="divide-y divide-white/5">
                {threads.map((row) => (
                  <li key={row.thread_id}>
                    <button
                      type="button"
                      onClick={() => void openThread(row.thread_id)}
                      className={`flex w-full flex-col gap-0.5 px-3 py-3 text-left hover:bg-white/5 ${
                        selectedId === row.thread_id ? "bg-white/10" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-semibold text-white">
                          {row.customer_name}
                        </span>
                        {row.unread_count > 0 ? (
                          <span className="shrink-0 rounded-full bg-emerald-500/90 px-1.5 text-[10px] font-bold text-black">
                            {row.unread_count}
                          </span>
                        ) : null}
                      </div>
                      <p className="text-[11px] uppercase tracking-wide text-emerald-300/90">
                        {channelBadge(row.channel)}
                      </p>
                      <p className="truncate text-xs text-zinc-400">{row.preview || "—"}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="border-t border-white/10 p-3 text-xs text-zinc-500">
            <Link href="/client/bots" className="text-emerald-300 hover:underline">
              {navCopy.nav.bots || "AI Employee"} →
            </Link>
          </div>
        </section>

        {/* Detail */}
        <section
          className={`flex min-h-[60vh] flex-col rounded-2xl border border-white/10 bg-white/[0.03] ${
            showList ? "hidden md:flex" : "flex"
          }`}
        >
          {!selectedId ? (
            <div className="flex flex-1 items-center justify-center p-6 text-sm text-zinc-500">
              {t.empty}
            </div>
          ) : detailLoading ? (
            <p className="p-4 text-sm text-zinc-500">…</p>
          ) : (
            <>
              <header className="border-b border-white/10 p-3 sm:p-4">
                <button
                  type="button"
                  className="mb-2 text-xs text-emerald-300 md:hidden"
                  onClick={() => setSelectedId(null)}
                >
                  {t.back}
                </button>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h2 className="text-base font-semibold text-white">
                      {thread?.customer_name || "—"}
                    </h2>
                    <p className="text-xs text-zinc-400">
                      {channelLabel(thread?.channel || "", t)}
                      {thread?.bot_name ? ` · ${thread.bot_name}` : ""}
                    </p>
                  </div>
                  <span className="rounded-lg border border-white/10 px-2 py-1 text-[11px] text-zinc-400">
                    {t.aiReady}
                  </span>
                </div>
              </header>

              <div className="flex-1 space-y-2 overflow-y-auto p-3 sm:p-4">
                {messages.length === 0 ? (
                  <p className="text-sm text-zinc-500">{t.noMessages}</p>
                ) : (
                  messages.map((m) => {
                    const inbound = m.direction === "INBOUND";
                    return (
                      <div
                        key={m.id}
                        className={`flex ${inbound ? "justify-start" : "justify-end"}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                            inbound
                              ? "bg-white/10 text-zinc-100"
                              : "bg-emerald-500/20 text-emerald-50"
                          }`}
                        >
                          <p className="whitespace-pre-wrap break-words">{m.text}</p>
                          <p className="mt-1 text-[10px] opacity-60">
                            {channelBadge(m.channel || thread?.channel || "")}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <footer className="border-t border-white/10 p-3">
                {thread?.channel === "webchat" ? (
                  <p className="text-xs text-zinc-500">{t.unsupported}</p>
                ) : (
                  <div className="flex gap-2">
                    <textarea
                      value={composer}
                      onChange={(e) => setComposer(e.target.value)}
                      rows={2}
                      placeholder={t.placeholder}
                      className="min-h-[44px] flex-1 resize-none rounded-xl border border-white/15 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-zinc-500"
                    />
                    <button
                      type="button"
                      disabled={sendState === "sending" || !composer.trim()}
                      onClick={() => void sendMessage()}
                      className="shrink-0 self-end rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black disabled:opacity-50"
                    >
                      {sendState === "sending" ? t.sending : sendState === "failed" ? t.retry : t.send}
                    </button>
                  </div>
                )}
                {sendError ? <p className="mt-2 text-xs text-rose-300">{sendError}</p> : null}
              </footer>
            </>
          )}
        </section>
      </div>
    </ClientWorkspaceShell>
  );
}

export default function Page() {
  return <ClientInboxPage />;
}
