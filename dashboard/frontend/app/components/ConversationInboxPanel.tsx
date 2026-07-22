"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button } from "./ui";
import { PortalApiError, portalFetch } from "../lib/portalApi";

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
};

type MessageRow = {
  message_id: string;
  role: string;
  content: string;
  created_at: string;
};

type ConversationRow = {
  conversation_id: string;
  channel_connection_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  messages?: MessageRow[];
};

type StatusFilter = "all" | "open" | "prepared" | "closed";

function previewText(messages: MessageRow[] | undefined): string {
  if (!messages || messages.length === 0) return "No messages yet";
  const last = messages[messages.length - 1];
  const text = last.content.trim();
  if (text.length <= 80) return `${last.role}: ${text}`;
  return `${last.role}: ${text.slice(0, 77)}…`;
}

export function ConversationInboxPanel() {
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationRow | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [channelFilter, setChannelFilter] = useState<string>("all");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [needsProfile, setNeedsProfile] = useState(false);

  const channelById = useMemo(() => {
    const map = new Map<string, ChannelRow>();
    for (const row of channels) map.set(row.connection_id, row);
    return map;
  }, [channels]);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [conversationRows, channelRows] = await Promise.all([
        portalFetch<ConversationRow[]>("/portal/chatbot/conversations"),
        portalFetch<ChannelRow[]>("/portal/chatbot/channels"),
      ]);

      // Enrich with last message via existing get endpoint (no new API).
      const enriched = await Promise.all(
        conversationRows.map(async (row) => {
          try {
            const full = await portalFetch<ConversationRow>(
              `/portal/chatbot/conversations/${row.conversation_id}`,
            );
            return { ...row, messages: full.messages ?? [] };
          } catch {
            return { ...row, messages: [] };
          }
        }),
      );

      setConversations(enriched);
      setChannels(channelRows);
      setNeedsAuth(false);
      setNeedsProfile(false);
    } catch (err) {
      if (err instanceof PortalApiError && err.status === 401) {
        setNeedsAuth(true);
        setError("Sign in required — open First Run to continue.");
      } else if (err instanceof PortalApiError && err.detail === "profile_required") {
        setNeedsProfile(true);
        setError("Complete Business Profile in First Run first.");
      } else if (err instanceof PortalApiError) {
        setError(err.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("unexpected_error");
      }
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    return conversations.filter((row) => {
      if (statusFilter !== "all" && row.status !== statusFilter) return false;
      if (channelFilter === "all") return true;
      if (channelFilter === "none") return !row.channel_connection_id;
      return row.channel_connection_id === channelFilter;
    });
  }, [conversations, statusFilter, channelFilter]);

  const openConversation = (conversationId: string) =>
    void (async () => {
      setSelectedId(conversationId);
      setBusy(true);
      setError(null);
      try {
        const full = await portalFetch<ConversationRow>(
          `/portal/chatbot/conversations/${conversationId}`,
        );
        setDetail(full);
      } catch (err) {
        if (err instanceof PortalApiError) setError(err.detail);
        else if (err instanceof Error) setError(err.message);
      } finally {
        setBusy(false);
      }
    })();

  const createConversation = () =>
    void (async () => {
      setBusy(true);
      setError(null);
      try {
        const enabled = channels.find((c) => c.status === "enabled");
        const created = await portalFetch<ConversationRow>(
          "/portal/chatbot/conversations",
          {
            method: "POST",
            body: JSON.stringify({
              channel_connection_id: enabled?.connection_id ?? null,
            }),
          },
        );
        await load();
        setSelectedId(created.conversation_id);
        setDetail(created);
      } catch (err) {
        if (err instanceof PortalApiError) {
          if (err.detail === "profile_required") {
            setNeedsProfile(true);
            setError("Complete Business Profile in First Run first.");
          } else {
            setError(err.detail);
          }
        } else if (err instanceof Error) {
          setError(err.message);
        }
      } finally {
        setBusy(false);
      }
    })();

  const channelLabel = (row: ConversationRow) => {
    if (!row.channel_connection_id) return "Unassigned";
    const ch = channelById.get(row.channel_connection_id);
    return ch?.display_name || ch?.channel || "Channel";
  };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Inbox</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Conversation Inbox
          </h1>
          <p className="text-sm text-zinc-400">
            Lists and opens conversations from the Conversation Engine. Does not
            generate AI replies or talk to channels.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/projects/chatbot/activity"
            className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Activity
          </Link>
          <Button variant="secondary" onClick={() => void load()} disabled={busy}>
            Refresh
          </Button>
          <Button onClick={createConversation} disabled={busy}>
            New conversation
          </Button>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
          {needsAuth || needsProfile ? (
            <>
              {" "}
              <Link href="/projects/chatbot/setup" className="underline">
                Open First Run
              </Link>
            </>
          ) : null}
        </p>
      ) : null}

      <section
        className="flex flex-wrap gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4"
        aria-label="Inbox filters"
      >
        <label className="flex flex-col gap-1 text-xs text-zinc-500">
          Status
          <select
            className="rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="prepared">Prepared</option>
            <option value="closed">Closed</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-zinc-500">
          Channel
          <select
            className="rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
          >
            <option value="all">All channels</option>
            <option value="none">Unassigned</option>
            {channels.map((ch) => (
              <option key={ch.connection_id} value={ch.connection_id}>
                {ch.display_name || ch.channel}
              </option>
            ))}
          </select>
        </label>
        <p className="ml-auto self-end text-xs text-zinc-500">
          {filtered.length} conversation{filtered.length === 1 ? "" : "s"}
        </p>
      </section>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <section aria-label="Conversation list">
          {filtered.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-zinc-500">
              No conversations match these filters. Create one to verify the
              Inbox — full Conversation View arrives in PT2.3.
            </div>
          ) : (
            <ul className="space-y-2">
              {filtered.map((row) => {
                const selected = selectedId === row.conversation_id;
                return (
                  <li key={row.conversation_id}>
                    <button
                      type="button"
                      onClick={() => openConversation(row.conversation_id)}
                      className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                        selected
                          ? "border-emerald-400/40 bg-emerald-500/10"
                          : "border-white/10 bg-black/20 hover:border-white/25"
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-sm font-medium text-white">
                          {channelLabel(row)}
                        </span>
                        <span className="text-xs uppercase tracking-wide text-zinc-500">
                          {row.status}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-zinc-400">
                        {previewText(row.messages)}
                      </p>
                      <p className="mt-1 text-xs text-zinc-600">
                        Updated {row.updated_at}
                      </p>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section
          className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
          aria-label="Open conversation"
        >
          <h2 className="text-lg font-medium text-white">Open conversation</h2>
          {!detail ? (
            <p className="mt-3 text-sm text-zinc-500">
              Select a conversation to preview messages. Reply and full thread
              tools stay in PT2.3.
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-zinc-500">Status</dt>
                  <dd className="text-zinc-200">{detail.status}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Channel</dt>
                  <dd className="text-zinc-200">{channelLabel(detail)}</dd>
                </div>
              </dl>
              <ul className="max-h-[28rem] space-y-2 overflow-y-auto">
                {(detail.messages ?? []).length === 0 ? (
                  <li className="rounded-xl border border-dashed border-white/10 px-3 py-4 text-sm text-zinc-500">
                    Conversation opened — no messages yet.
                  </li>
                ) : (
                  (detail.messages ?? []).map((msg) => (
                    <li
                      key={msg.message_id}
                      className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
                    >
                      <p className="text-xs uppercase tracking-wide text-zinc-500">
                        {msg.role}
                      </p>
                      <p className="mt-1 whitespace-pre-wrap text-zinc-200">
                        {msg.content}
                      </p>
                    </li>
                  ))
                )}
              </ul>
              <p className="text-xs text-zinc-500">
                Read-only preview · Conversation Engine owns logic · PT2.3 adds
                interaction.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
