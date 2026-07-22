"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Badge, Button } from "./ui";
import { CHANNEL_TYPES } from "../lib/channelSetupMeta";
import { KNOWLEDGE_CATEGORIES } from "../lib/knowledgeCategories";
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
  configuration?: { model_name?: string };
};

const PROVIDER_LABEL: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama",
  kimi: "Kimi",
  custom: "Custom",
};

function pct(part: number, whole: number): number {
  if (whole <= 0) return 0;
  return Math.round((part / whole) * 100);
}

function ActionLink({
  href,
  children,
}: {
  href: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-zinc-200 transition hover:border-white/25 hover:bg-white/[0.08]"
    >
      {children}
    </Link>
  );
}

export function VectorDashboardPanel() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [channels, setChannels] = useState<ChannelRow[]>([]);
  const [providers, setProviders] = useState<ProviderRow[]>([]);
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
        return;
      }
      setProfile(existing);
      setNeedsSetup(false);
      setNeedsAuth(false);

      const [knowledgeRows, channelRows, providerRows] = await Promise.all([
        portalFetch<KnowledgeItem[]>("/portal/chatbot/knowledge"),
        portalFetch<ChannelRow[]>("/portal/chatbot/channels"),
        portalFetch<ProviderRow[]>("/portal/chatbot/providers"),
      ]);
      setKnowledge(knowledgeRows);
      setChannels(channelRows);
      setProviders(providerRows);
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
    const cats = new Set(
      knowledge.map((k) => k.category).filter(Boolean),
    );
    return KNOWLEDGE_CATEGORIES.filter((c) => cats.has(c)).length;
  }, [knowledge]);

  const channelsReady = useMemo(() => {
    const byType = new Map<string, ChannelRow>();
    for (const row of channels) byType.set(row.channel, row);
    return CHANNEL_TYPES.filter((type) => {
      const row = byType.get(type);
      return row?.status === "enabled" || row?.status === "configured";
    }).length;
  }, [channels]);

  const businessReady = profile ? 1 : 0;
  const knowledgePct = pct(knowledgeFilled, KNOWLEDGE_CATEGORIES.length);
  const channelsPct = pct(channelsReady, CHANNEL_TYPES.length);
  const businessPct = businessReady * 100;
  const overallPct = Math.round(
    (businessPct + knowledgePct + channelsPct) / 3,
  );

  const activeProvider =
    providers.find((p) => p.status === "enabled" || p.is_active) ||
    providers.find((p) => p.status === "configured") ||
    null;

  const activity = useMemo(() => {
    type Event = { at: string; label: string; href: string };
    const events: Event[] = [];
    if (profile?.updated_at) {
      events.push({
        at: profile.updated_at,
        label: `Business profile · ${profile.business_name}`,
        href: "/projects/chatbot/setup",
      });
    }
    for (const item of knowledge) {
      if (!item.updated_at) continue;
      events.push({
        at: item.updated_at,
        label: `Knowledge · ${item.title}`,
        href: "/projects/chatbot/knowledge",
      });
    }
    for (const row of channels) {
      if (!row.updated_at) continue;
      events.push({
        at: row.updated_at,
        label: `Channel · ${row.display_name || row.channel} (${row.status})`,
        href: "/projects/chatbot/channels",
      });
    }
    events.sort((a, b) => (a.at < b.at ? 1 : a.at > b.at ? -1 : 0));
    return events.slice(0, 8);
  }, [profile, knowledge, channels]);

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Badge>Vector · Dashboard</Badge>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Your AI Business Employee
          </h1>
          <p className="text-sm text-zinc-400">
            Aggregates platform state only — edits happen in Knowledge, Channels,
            and First Run.
          </p>
        </div>
        <Button variant="secondary" onClick={() => void load()} disabled={busy}>
          Refresh
        </Button>
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
          <h2 className="text-lg font-medium text-white">Vector is not set up yet</h2>
          <p className="text-sm text-zinc-400">
            Run First Run to create a Business Profile, then return here for the
            daily overview.
          </p>
          <ActionLink href="/projects/chatbot/setup">Start First Run</ActionLink>
        </section>
      ) : null}

      {profile ? (
        <>
          <section
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            aria-label="Business status"
          >
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              Business
            </p>
            <h2 className="mt-1 text-xl font-medium text-white">
              {profile.business_name}
            </h2>
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-zinc-500">Industry</dt>
                <dd className="text-zinc-200">{profile.industry}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Language</dt>
                <dd className="text-zinc-200">{profile.language}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Timezone</dt>
                <dd className="text-zinc-200">{profile.timezone}</dd>
              </div>
            </dl>
          </section>

          <section
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            aria-label="Vector readiness"
          >
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-zinc-500">
                  Vector readiness
                </p>
                <p className="text-3xl font-semibold text-white">{overallPct}%</p>
              </div>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-black/40">
              <div
                className="h-full rounded-full bg-emerald-400/80 transition-all"
                style={{ width: `${overallPct}%` }}
              />
            </div>
            <ul className="mt-4 grid gap-3 sm:grid-cols-3">
              {[
                {
                  label: "Business",
                  value: businessPct,
                  detail: profile ? "Profile ready" : "Missing",
                  href: "/projects/chatbot/setup",
                },
                {
                  label: "Knowledge",
                  value: knowledgePct,
                  detail: `${knowledgeFilled}/${KNOWLEDGE_CATEGORIES.length} categories`,
                  href: "/projects/chatbot/knowledge",
                },
                {
                  label: "Channels",
                  value: channelsPct,
                  detail: `${channelsReady}/${CHANNEL_TYPES.length} ready`,
                  href: "/projects/chatbot/channels",
                },
              ].map((item) => (
                <li key={item.label}>
                  <Link
                    href={item.href}
                    className="block rounded-xl border border-white/10 bg-black/20 px-3 py-3 transition hover:border-white/25"
                  >
                    <p className="text-xs text-zinc-500">{item.label}</p>
                    <p className="text-lg font-medium text-white">{item.value}%</p>
                    <p className="text-xs text-zinc-500">{item.detail}</p>
                  </Link>
                </li>
              ))}
            </ul>
          </section>

          <section
            className="rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            aria-label="AI provider"
          >
            <p className="text-xs uppercase tracking-wide text-zinc-500">AI</p>
            {activeProvider ? (
              <div className="mt-2 space-y-1">
                <p className="text-lg font-medium text-white">
                  {PROVIDER_LABEL[activeProvider.provider_type] ||
                    activeProvider.display_name}
                </p>
                <p className="text-sm text-zinc-400">
                  Model:{" "}
                  {activeProvider.configuration?.model_name || "default / stub"}
                </p>
                <p className="text-sm text-zinc-400">
                  Status: {activeProvider.status}
                  {activeProvider.is_active ? " · active" : ""}
                </p>
              </div>
            ) : (
              <p className="mt-2 text-sm text-zinc-500">
                No provider selected yet. Configure AI in First Run.
              </p>
            )}
          </section>

          <section aria-label="Quick actions">
            <h2 className="mb-3 text-lg font-medium text-white">Quick actions</h2>
            <div className="flex flex-wrap gap-2">
              <ActionLink href="/projects/chatbot/setup">Edit Business</ActionLink>
              <ActionLink href="/projects/chatbot/knowledge">
                Manage Knowledge
              </ActionLink>
              <ActionLink href="/projects/chatbot/channels">
                Setup Channels
              </ActionLink>
              <ActionLink href="/projects/chatbot/setup">Configure AI</ActionLink>
            </div>
          </section>

          <section aria-label="Recent activity">
            <h2 className="mb-3 text-lg font-medium text-white">Recent activity</h2>
            {activity.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-sm text-zinc-500">
                Activity feed is ready. Updates to profile, knowledge, and channels
                will appear here once timestamps are available.
              </div>
            ) : (
              <ul className="space-y-2">
                {activity.map((event) => (
                  <li key={`${event.at}-${event.label}`}>
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
