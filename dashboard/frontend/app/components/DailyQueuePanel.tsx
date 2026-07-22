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
};

type BucketId = "waiting" | "needs_attention" | "resolved" | "closed";

const BUCKETS: { id: BucketId; label: string; hint: string }[] = [
  { id: "waiting", label: "Waiting", hint: "Open · awaiting work" },
  {
    id: "needs_attention",
    label: "Needs attention",
    hint: "Prepared · review Vector reply",
  },
  {
    id: "resolved",
    label: "Resolved",
    hint: "Operator-resolved flag — empty until PT3",
  },
  { id: "closed", label: "Closed", hint: "Archived conversations" },
];

function bucketFor(row: ConversationRow): BucketId {
  if (row.status === "closed") return "closed";
  if (row.status === "open") return "waiting";
  if (row.status === "prepared") return "needs_attention";
  return "waiting";
}

export function DailyQueuePanel() {
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
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

  const channelLabel = useCallback(
    (id: string | null) => {
      if (!id) return "Unassigned";
      const ch = channels.find((c) => c.connection_id === id);
      return ch?.display_name || ch?.channel || "Channel";
    },
    [channels],
  );

  const grouped = useMemo(() => {
    const map: Record<BucketId, ConversationRow[]> = {
      waiting: [],
      needs_attention: [],
      resolved: [],
      closed: [],
    };
    for (const row of conversations) {
      map[bucketFor(row)].push(row);
    }
    return map;
  }, [conversations]);

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Queue</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Daily Queue
          </h1>
          <p className="text-sm text-zinc-400">
            Groups existing conversations by status — no new domain models.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/projects/chatbot/inbox"
            className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Inbox
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

      <div className="grid gap-4 lg:grid-cols-2">
        {BUCKETS.map((bucket) => (
          <section
            key={bucket.id}
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
          >
            <div className="flex items-baseline justify-between gap-2">
              <h2 className="text-lg font-medium text-white">{bucket.label}</h2>
              <span className="text-sm text-zinc-500">
                {grouped[bucket.id].length}
              </span>
            </div>
            <p className="text-xs text-zinc-500">{bucket.hint}</p>
            <ul className="mt-3 space-y-2">
              {grouped[bucket.id].length === 0 ? (
                <li className="rounded-xl border border-dashed border-white/10 px-3 py-4 text-sm text-zinc-500">
                  Empty
                </li>
              ) : (
                grouped[bucket.id].map((row) => (
                  <li key={row.conversation_id}>
                    <Link
                      href={`/projects/chatbot/inbox/${row.conversation_id}`}
                      className="block rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-sm transition hover:border-white/25"
                    >
                      <span className="font-medium text-white">
                        {channelLabel(row.channel_connection_id)}
                      </span>
                      <span className="mt-1 block text-xs text-zinc-500">
                        {row.status} · {row.updated_at}
                      </span>
                    </Link>
                  </li>
                ))
              )}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
