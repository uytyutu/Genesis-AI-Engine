"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button } from "./ui";
import { PortalApiError, portalFetch } from "../lib/portalApi";

type ConversationRow = {
  conversation_id: string;
  channel_connection_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
};

type CustomerCard = {
  key: string;
  name: string;
  channel: string;
  channelStatus: string;
  conversationCount: number;
  firstAt: string;
  lastAt: string;
  conversationIds: string[];
};

export function CustomerWorkspacePanel() {
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [rows, channelRows] = await Promise.all([
        portalFetch<ConversationRow[]>("/portal/chatbot/conversations"),
        portalFetch<ChannelRow[]>("/portal/chatbot/channels"),
      ]);
      setConversations(rows);
      setChannels(channelRows);
    } catch (err) {
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const customers = useMemo(() => {
    const map = new Map<string, CustomerCard>();
    for (const row of conversations) {
      const key = row.channel_connection_id || `solo:${row.conversation_id}`;
      const ch = row.channel_connection_id
        ? channels.find((c) => c.connection_id === row.channel_connection_id)
        : undefined;
      const existing = map.get(key);
      if (!existing) {
        map.set(key, {
          key,
          name: ch?.display_name || "Guest customer",
          channel: ch?.channel || "unassigned",
          channelStatus: ch?.status || "—",
          conversationCount: 1,
          firstAt: row.created_at,
          lastAt: row.updated_at,
          conversationIds: [row.conversation_id],
        });
      } else {
        existing.conversationCount += 1;
        existing.conversationIds.push(row.conversation_id);
        if (row.created_at < existing.firstAt) existing.firstAt = row.created_at;
        if (row.updated_at > existing.lastAt) existing.lastAt = row.updated_at;
      }
    }
    return Array.from(map.values()).sort((a, b) =>
      a.lastAt < b.lastAt ? 1 : -1,
    );
  }, [conversations, channels]);

  const selected = customers.find((c) => c.key === selectedKey) || null;

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Customers</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Customer Workspace
          </h1>
          <p className="text-sm text-zinc-400">
            Derived from Channel Connections + Conversations — no Customer domain
            invented.
          </p>
        </div>
        <Button variant="secondary" onClick={() => void load()} disabled={busy}>
          Refresh
        </Button>
      </header>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <ul className="space-y-2">
          {customers.length === 0 ? (
            <li className="rounded-2xl border border-dashed border-white/10 px-4 py-8 text-sm text-zinc-500">
              No customer proxies yet. Create conversations from Inbox.
            </li>
          ) : (
            customers.map((card) => (
              <li key={card.key}>
                <button
                  type="button"
                  onClick={() => setSelectedKey(card.key)}
                  className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                    selectedKey === card.key
                      ? "border-emerald-400/40 bg-emerald-500/10"
                      : "border-white/10 bg-black/20 hover:border-white/25"
                  }`}
                >
                  <p className="font-medium text-white">{card.name}</p>
                  <p className="text-xs text-zinc-500">
                    {card.channel} · {card.conversationCount} conversation
                    {card.conversationCount === 1 ? "" : "s"}
                  </p>
                </button>
              </li>
            ))
          )}
        </ul>

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
          {!selected ? (
            <p className="text-sm text-zinc-500">Select a customer card.</p>
          ) : (
            <div className="space-y-3 text-sm">
              <h2 className="text-lg font-medium text-white">{selected.name}</h2>
              <dl className="space-y-2">
                <div>
                  <dt className="text-zinc-500">Channel</dt>
                  <dd className="text-zinc-200">
                    {selected.channel} · {selected.channelStatus}
                  </dd>
                </div>
                <div>
                  <dt className="text-zinc-500">First contact</dt>
                  <dd className="text-zinc-200">{selected.firstAt}</dd>
                </div>
                <div>
                  <dt className="text-zinc-500">Last contact</dt>
                  <dd className="text-zinc-200">{selected.lastAt}</dd>
                </div>
              </dl>
              <div>
                <p className="text-zinc-500">Conversation history</p>
                <ul className="mt-2 space-y-1">
                  {selected.conversationIds.map((id) => (
                    <li key={id}>
                      <Link
                        href={`/projects/chatbot/inbox/${id}`}
                        className="font-mono text-xs text-sky-300 hover:underline"
                      >
                        {id.slice(0, 8)}… →
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-zinc-500">Notes (stub · local only)</p>
                <textarea
                  className="mt-1 w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-white"
                  rows={3}
                  value={notes[selected.key] || ""}
                  onChange={(e) =>
                    setNotes((prev) => ({
                      ...prev,
                      [selected.key]: e.target.value,
                    }))
                  }
                />
              </div>
              <Link
                href="/projects/chatbot/knowledge"
                className="inline-flex text-xs text-sky-300 hover:underline"
              >
                Business facts (Knowledge) →
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
