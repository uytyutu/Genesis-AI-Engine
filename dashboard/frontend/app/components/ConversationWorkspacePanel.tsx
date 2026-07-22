"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button } from "./ui";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";

type Profile = {
  business_name: string;
  industry: string;
  language: string;
  timezone: string;
};

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
};

type ProviderRow = {
  provider_id: string;
  provider_type: string;
  display_name: string;
  status: string;
  is_active?: boolean;
  configuration?: { model_name?: string };
};

type MessageRow = {
  message_id: string;
  role: string;
  content: string;
  created_at: string;
};

type ConversationRow = {
  conversation_id: string;
  profile_id: string;
  channel_connection_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  messages?: MessageRow[];
};

const PROVIDER_LABEL: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama",
  kimi: "Kimi",
};

type Props = {
  conversationId: string;
};

export function ConversationWorkspacePanel({ conversationId }: Props) {
  const [conversation, setConversation] = useState<ConversationRow | null>(null);
  const [allConversations, setAllConversations] = useState<ConversationRow[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [channel, setChannel] = useState<ChannelRow | null>(null);
  const [provider, setProvider] = useState<ProviderRow | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [takeover, setTakeover] = useState(false);
  const [notes, setNotes] = useState("");

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [detail, list, profileRow, channels, providers] = await Promise.all([
        portalFetch<ConversationRow>(
          `/portal/chatbot/conversations/${conversationId}`,
        ),
        portalFetch<ConversationRow[]>("/portal/chatbot/conversations"),
        portalFetchAllow404<Profile>("/portal/chatbot/profile"),
        portalFetch<ChannelRow[]>("/portal/chatbot/channels"),
        portalFetch<ProviderRow[]>("/portal/chatbot/providers"),
      ]);
      setConversation(detail);
      setAllConversations(list);
      setProfile(profileRow);
      const ch = detail.channel_connection_id
        ? channels.find((c) => c.connection_id === detail.channel_connection_id) ||
          null
        : null;
      setChannel(ch);
      setProvider(
        providers.find((p) => p.status === "enabled" || p.is_active) || null,
      );
    } catch (err) {
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
    } finally {
      setBusy(false);
    }
  }, [conversationId]);

  useEffect(() => {
    void load();
  }, [load]);

  const relatedCount = useMemo(() => {
    if (!conversation?.channel_connection_id) return 1;
    return allConversations.filter(
      (c) => c.channel_connection_id === conversation.channel_connection_id,
    ).length;
  }, [allConversations, conversation]);

  const setStatus = (status: string) =>
    void (async () => {
      setBusy(true);
      setError(null);
      setNotice(null);
      try {
        const updated = await portalFetch<ConversationRow>(
          `/portal/chatbot/conversations/${conversationId}/status`,
          {
            method: "PUT",
            body: JSON.stringify({ status }),
          },
        );
        setConversation(updated);
        setNotice(
          status === "closed"
            ? "Conversation closed (archive uses closed status)."
            : `Status → ${status}`,
        );
      } catch (err) {
        if (err instanceof PortalApiError) setError(err.detail);
        else if (err instanceof Error) setError(err.message);
      } finally {
        setBusy(false);
      }
    })();

  if (!conversation && !error) {
    return (
      <p className="px-1 py-6 text-sm text-zinc-500">
        {busy ? "Loading conversation…" : "Conversation not found."}
      </p>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Conversation</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Conversation Workspace
          </h1>
          <p className="font-mono text-xs text-zinc-500">
            {conversationId}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/projects/chatbot/inbox"
            className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            ← Inbox
          </Link>
          <Button variant="secondary" onClick={() => void load()} disabled={busy}>
            Refresh
          </Button>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}
      {notice ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {notice}
        </p>
      ) : null}

      {conversation ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.85fr)]">
          <section
            className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4"
            aria-label="Timeline"
          >
            <h2 className="text-lg font-medium text-white">Timeline</h2>
            <ul className="space-y-2">
              {(conversation.messages ?? []).length === 0 ? (
                <li className="rounded-xl border border-dashed border-white/10 px-3 py-6 text-sm text-zinc-500">
                  No messages yet. Timeline is ready for customer · Vector ·
                  system events.
                </li>
              ) : (
                (conversation.messages ?? []).map((msg) => (
                  <li
                    key={msg.message_id}
                    className={`rounded-xl border px-3 py-3 text-sm ${
                      msg.role === "assistant"
                        ? "border-sky-400/20 bg-sky-500/10"
                        : msg.role === "system"
                          ? "border-white/10 bg-white/[0.04]"
                          : "border-white/10 bg-black/25"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs uppercase tracking-wide text-zinc-400">
                        {msg.role === "assistant"
                          ? "Vector"
                          : msg.role === "user"
                            ? "Customer"
                            : "System"}
                      </span>
                      <span className="text-xs text-zinc-600">{msg.created_at}</span>
                    </div>
                    <p className="mt-1 whitespace-pre-wrap text-zinc-100">
                      {msg.content}
                    </p>
                  </li>
                ))
              )}
            </ul>
          </section>

          <aside className="space-y-4">
            <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <h2 className="text-sm font-medium text-white">Customer card</h2>
              <dl className="mt-3 space-y-2 text-sm">
                <div>
                  <dt className="text-zinc-500">Name</dt>
                  <dd className="text-zinc-200">
                    {channel?.display_name || "Guest customer"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Channel</dt>
                  <dd className="text-zinc-200">
                    {channel
                      ? `${channel.channel} · ${channel.status}`
                      : "Unassigned"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">First contact</dt>
                  <dd className="text-zinc-200">{conversation.created_at}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Last contact</dt>
                  <dd className="text-zinc-200">{conversation.updated_at}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Conversations (same channel)</dt>
                  <dd className="text-zinc-200">{relatedCount}</dd>
                </div>
              </dl>
              <Link
                href="/projects/chatbot/setup"
                className="mt-3 inline-flex text-xs text-sky-300 hover:underline"
              >
                Business Profile →
              </Link>
            </section>

            <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <h2 className="text-sm font-medium text-white">AI context</h2>
              <p className="mt-2 text-xs text-zinc-500">Display only</p>
              <dl className="mt-2 space-y-2 text-sm">
                <div>
                  <dt className="text-zinc-500">Provider</dt>
                  <dd className="text-zinc-200">
                    {provider
                      ? PROVIDER_LABEL[provider.provider_type] ||
                        provider.display_name
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Model</dt>
                  <dd className="text-zinc-200">
                    {provider?.configuration?.model_name || "default / stub"}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Prompt Package ID</dt>
                  <dd className="font-mono text-xs text-zinc-400">
                    available after AI turn metadata
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Conversation ID</dt>
                  <dd className="break-all font-mono text-xs text-zinc-400">
                    {conversation.conversation_id}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <h2 className="text-sm font-medium text-white">Metadata</h2>
              <dl className="mt-2 space-y-2 text-sm">
                <div>
                  <dt className="text-zinc-500">Status</dt>
                  <dd className="text-zinc-200">{conversation.status}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Created</dt>
                  <dd className="text-zinc-200">{conversation.created_at}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Updated</dt>
                  <dd className="text-zinc-200">{conversation.updated_at}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Assigned</dt>
                  <dd className="text-zinc-200">Unassigned (stub)</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Language</dt>
                  <dd className="text-zinc-200">{profile?.language || "—"}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Industry</dt>
                  <dd className="text-zinc-200">{profile?.industry || "—"}</dd>
                </div>
              </dl>
            </section>

            <section className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <h2 className="text-sm font-medium text-white">Actions</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busy || conversation.status === "closed"}
                  onClick={() => setStatus("closed")}
                >
                  Close / Archive
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busy || conversation.status === "open"}
                  onClick={() => setStatus("open")}
                >
                  Reopen
                </Button>
              </div>
            </section>

            <section className="rounded-2xl border border-dashed border-white/10 p-4">
              <h2 className="text-sm font-medium text-white">Human takeover</h2>
              <p className="mt-1 text-xs text-zinc-500">Stub · no routing yet</p>
              <Button
                size="sm"
                variant="ghost"
                className="mt-2"
                onClick={() => setTakeover((v) => !v)}
              >
                {takeover ? "Release (stub)" : "Take over (stub)"}
              </Button>
            </section>

            <section className="rounded-2xl border border-dashed border-white/10 p-4">
              <h2 className="text-sm font-medium text-white">Internal notes</h2>
              <p className="mt-1 text-xs text-zinc-500">
                Stub · not persisted to domain
              </p>
              <textarea
                className="mt-2 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white"
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Operator note…"
              />
            </section>
          </aside>
        </div>
      ) : null}
    </div>
  );
}
