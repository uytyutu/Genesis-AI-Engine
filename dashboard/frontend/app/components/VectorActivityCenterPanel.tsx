"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button } from "./ui";
import { KNOWLEDGE_CATEGORIES } from "../lib/knowledgeCategories";
import {
  PortalApiError,
  portalFetch,
  portalFetchAllow404,
} from "../lib/portalApi";

type Profile = {
  business_name: string;
  industry: string;
  updated_at?: string;
};

type KnowledgeItem = {
  knowledge_id: string;
  category: string;
  title: string;
  updated_at?: string;
};

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
  updated_at?: string;
};

type ProviderRow = {
  provider_id: string;
  provider_type: string;
  display_name: string;
  status: string;
  is_active?: boolean;
  updated_at?: string;
  configuration?: { model_name?: string };
};

type ConversationRow = {
  conversation_id: string;
  status: string;
  channel_connection_id: string | null;
  created_at: string;
  updated_at: string;
};

type AttentionItem = {
  id: string;
  label: string;
  href: string;
};

type ActivityEvent = {
  id: string;
  at: string;
  label: string;
  href: string;
};

const PROVIDER_LABEL: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama",
  kimi: "Kimi",
};

function isSameUtcDay(iso: string, now = new Date()): boolean {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return false;
  return (
    d.getUTCFullYear() === now.getUTCFullYear() &&
    d.getUTCMonth() === now.getUTCMonth() &&
    d.getUTCDate() === now.getUTCDate()
  );
}

function HealthPill({
  label,
  ready,
}: {
  label: string;
  ready: boolean;
}) {
  return (
    <li
      className={`rounded-xl border px-3 py-3 text-sm ${
        ready
          ? "border-emerald-400/25 bg-emerald-500/10 text-emerald-200"
          : "border-white/10 bg-black/20 text-zinc-400"
      }`}
    >
      <p className="text-xs uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-1 font-medium">{ready ? "Ready" : "Needs attention"}</p>
    </li>
  );
}

export function VectorActivityCenterPanel() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [providers, setProviders] = useState<ProviderRow[]>([]);
  const [conversations, setConversations] = useState<ConversationRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [needsSetup, setNeedsSetup] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const existing = await portalFetchAllow404<Profile>(
        "/portal/chatbot/profile",
      );
      if (!existing) {
        setProfile(null);
        setNeedsSetup(true);
        setNeedsAuth(false);
        setKnowledge([]);
        setChannels([]);
        setProviders([]);
        setConversations([]);
        return;
      }
      setProfile(existing);
      setNeedsSetup(false);
      setNeedsAuth(false);

      const [knowledgeRows, channelRows, providerRows, conversationRows] =
        await Promise.all([
          portalFetch<KnowledgeItem[]>("/portal/chatbot/knowledge"),
          portalFetch<ChannelRow[]>("/portal/chatbot/channels"),
          portalFetch<ProviderRow[]>("/portal/chatbot/providers"),
          portalFetch<ConversationRow[]>("/portal/chatbot/conversations"),
        ]);
      setKnowledge(knowledgeRows);
      setChannels(channelRows);
      setProviders(providerRows);
      setConversations(conversationRows);
    } catch (err) {
      if (err instanceof PortalApiError && err.status === 401) {
        setNeedsAuth(true);
        setError("Sign in required — open First Run to continue.");
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

  const knowledgeFilled = useMemo(() => {
    const cats = new Set(knowledge.map((k) => k.category));
    return KNOWLEDGE_CATEGORIES.filter((c) => cats.has(c)).length;
  }, [knowledge]);

  const activeChannels = useMemo(
    () => channels.filter((c) => c.status === "enabled").length,
    [channels],
  );

  const channelsConfiguredOrEnabled = useMemo(
    () =>
      channels.filter(
        (c) => c.status === "enabled" || c.status === "configured",
      ).length,
    [channels],
  );

  const conversationsToday = useMemo(
    () => conversations.filter((c) => isSameUtcDay(c.created_at)).length,
    [conversations],
  );

  const unansweredStub = useMemo(() => {
    // Until Inbox exists: open conversations count as needing attention.
    return conversations.filter((c) => c.status === "open" || c.status === "active")
      .length;
  }, [conversations]);

  const activeProvider =
    providers.find((p) => p.status === "enabled" || p.is_active) || null;

  const aiReady = Boolean(
    activeProvider &&
      (activeProvider.status === "enabled" || activeProvider.is_active),
  );

  const businessReady = Boolean(profile);
  const knowledgeReady = knowledgeFilled >= 3;
  const channelsReady = channelsConfiguredOrEnabled >= 1;

  const responseRateLabel =
    conversations.length === 0
      ? "—"
      : "100% stub";

  const attention = useMemo(() => {
    const items: AttentionItem[] = [];
    if (!profile) {
      items.push({
        id: "missing-profile",
        label: "Missing business profile",
        href: "/projects/chatbot/setup",
      });
      return items;
    }
    if (knowledgeFilled < KNOWLEDGE_CATEGORIES.length) {
      items.push({
        id: "knowledge-incomplete",
        label: `Knowledge incomplete (${knowledgeFilled}/${KNOWLEDGE_CATEGORIES.length} categories)`,
        href: "/projects/chatbot/knowledge",
      });
    }
    const disabled = channels.filter((c) => c.status === "disabled");
    if (disabled.length > 0) {
      items.push({
        id: "channels-disabled",
        label: `${disabled.length} channel(s) disabled`,
        href: "/projects/chatbot/channels",
      });
    }
    if (channelsConfiguredOrEnabled === 0) {
      items.push({
        id: "channels-none",
        label: "No channels configured or enabled",
        href: "/projects/chatbot/channels",
      });
    }
    if (!aiReady) {
      items.push({
        id: "ai-unavailable",
        label: "AI provider unavailable or not enabled",
        href: "/projects/chatbot/setup",
      });
    }
    if (unansweredStub > 0) {
      items.push({
        id: "unanswered",
        label: `${unansweredStub} conversation(s) may need attention`,
        href: "/projects/chatbot/activity",
      });
    }
    return items;
  }, [
    profile,
    knowledgeFilled,
    channels,
    channelsConfiguredOrEnabled,
    aiReady,
    unansweredStub,
  ]);

  const events = useMemo(() => {
    const list: ActivityEvent[] = [];
    if (profile?.updated_at) {
      list.push({
        id: `profile-${profile.updated_at}`,
        at: profile.updated_at,
        label: "Business profile updated",
        href: "/projects/chatbot/setup",
      });
    }
    for (const item of knowledge) {
      if (!item.updated_at) continue;
      list.push({
        id: `knowledge-${item.knowledge_id}`,
        at: item.updated_at,
        label: `Knowledge updated · ${item.title}`,
        href: "/projects/chatbot/knowledge",
      });
    }
    for (const row of channels) {
      if (!row.updated_at) continue;
      const verb =
        row.status === "enabled"
          ? "Channel enabled"
          : row.status === "disabled"
            ? "Channel disabled"
            : "Channel configured";
      list.push({
        id: `channel-${row.connection_id}`,
        at: row.updated_at,
        label: `${verb} · ${row.display_name || row.channel}`,
        href: "/projects/chatbot/channels",
      });
    }
    for (const p of providers) {
      if (!p.updated_at) continue;
      if (p.status !== "enabled" && !p.is_active) continue;
      list.push({
        id: `provider-${p.provider_id}`,
        at: p.updated_at,
        label: `Provider changed · ${PROVIDER_LABEL[p.provider_type] || p.display_name}`,
        href: "/projects/chatbot/setup",
      });
    }
    for (const c of conversations) {
      list.push({
        id: `conv-start-${c.conversation_id}`,
        at: c.created_at,
        label: "Customer conversation started",
        href: "/projects/chatbot/activity",
      });
      if (c.updated_at && c.updated_at !== c.created_at) {
        list.push({
          id: `conv-update-${c.conversation_id}`,
          at: c.updated_at,
          label:
            c.status === "closed" || c.status === "finished"
              ? "Customer conversation finished"
              : "Customer conversation updated",
          href: "/projects/chatbot/activity",
        });
      }
    }
    list.sort((a, b) => (a.at < b.at ? 1 : a.at > b.at ? -1 : 0));
    return list.slice(0, 12);
  }, [profile, knowledge, channels, providers, conversations]);

  const summaryCards = [
    {
      label: "Conversations today",
      value: String(conversationsToday),
      hint: `${conversations.length} total`,
    },
    {
      label: "Active channels",
      value: String(activeChannels),
      hint: `${channelsConfiguredOrEnabled} configured+`,
    },
    {
      label: "New leads",
      value: conversationsToday > 0 ? String(conversationsToday) : "0",
      hint: "Stub · equals new conversations today",
    },
    {
      label: "Response rate",
      value: responseRateLabel,
      hint: "Stub until Inbox metrics exist",
    },
  ];

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Activity</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            What happened today?
          </h1>
          <p className="text-sm text-zinc-400">
            Operational view of Vector at work — aggregates state only. Does not
            edit data or talk to providers.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/projects/chatbot/inbox"
            className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Inbox
          </Link>
          <Link
            href="/projects/chatbot"
            className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Dashboard
          </Link>
          <Button variant="secondary" onClick={() => void load()} disabled={busy}>
            Refresh
          </Button>
        </div>
      </header>

      {error ? (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
          {needsAuth ? (
            <>
              {" "}
              <Link href="/projects/chatbot/setup" className="underline">
                Open First Run
              </Link>
            </>
          ) : null}
        </p>
      ) : null}

      {needsSetup && !needsAuth ? (
        <section className="space-y-3 rounded-2xl border border-amber-400/20 bg-amber-500/[0.06] p-5">
          <h2 className="text-lg font-medium text-white">No operational data yet</h2>
          <p className="text-sm text-zinc-400">
            Complete First Run so Activity Center can show conversations, health,
            and attention items.
          </p>
          <Link
            href="/projects/chatbot/setup"
            className="inline-flex rounded-xl bg-white px-4 py-2 text-sm font-medium text-black"
          >
            Start First Run
          </Link>
        </section>
      ) : null}

      {profile ? (
        <>
          <section aria-label="Activity summary">
            <h2 className="mb-3 text-lg font-medium text-white">Today</h2>
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {summaryCards.map((card) => (
                <li
                  key={card.label}
                  className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-4"
                >
                  <p className="text-xs uppercase tracking-wide text-zinc-500">
                    {card.label}
                  </p>
                  <p className="mt-1 text-2xl font-semibold text-white">
                    {card.value}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">{card.hint}</p>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-zinc-500">
              Unanswered (stub): {unansweredStub} · AI:{" "}
              {activeProvider
                ? `${PROVIDER_LABEL[activeProvider.provider_type] || activeProvider.display_name} · ${activeProvider.status}`
                : "none"}
            </p>
          </section>

          <section aria-label="Operational health">
            <h2 className="mb-3 text-lg font-medium text-white">Health</h2>
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <HealthPill label="Business" ready={businessReady} />
              <HealthPill label="Knowledge" ready={knowledgeReady} />
              <HealthPill label="Channels" ready={channelsReady} />
              <HealthPill label="AI" ready={aiReady} />
            </ul>
          </section>

          <section aria-label="Attention required">
            <h2 className="mb-3 text-lg font-medium text-white">
              Attention required
            </h2>
            {attention.length === 0 ? (
              <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/[0.06] px-4 py-5 text-sm text-emerald-100">
                Nothing urgent — Vector looks healthy for daily work.
              </div>
            ) : (
              <ul className="space-y-2">
                {attention.map((item) => (
                  <li key={item.id}>
                    <Link
                      href={item.href}
                      className="flex items-center justify-between gap-2 rounded-xl border border-amber-400/25 bg-amber-500/[0.08] px-4 py-3 text-sm text-amber-50 transition hover:border-amber-300/40"
                    >
                      <span>{item.label}</span>
                      <span className="text-xs text-amber-200/80">Review →</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-label="Recent events">
            <h2 className="mb-3 text-lg font-medium text-white">Recent events</h2>
            {events.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
                Event feed is ready. When Knowledge changes, channels go live, or
                customers start conversations, they will appear here — ready for
                real Inbox traffic later.
              </div>
            ) : (
              <ul className="space-y-2">
                {events.map((event) => (
                  <li key={event.id}>
                    <Link
                      href={event.href}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm transition hover:border-white/25"
                    >
                      <span className="text-zinc-200">{event.label}</span>
                      <span className="text-xs text-zinc-500">{event.at}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
