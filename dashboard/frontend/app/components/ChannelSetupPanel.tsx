"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Field, Input } from "./ui";
import {
  CHANNEL_CONFIG_FIELDS,
  CHANNEL_META,
  CHANNEL_STATUS_LABEL,
  CHANNEL_STATUSES,
  CHANNEL_TYPES,
  type ChannelStatusId,
  type ChannelTypeId,
} from "../lib/channelSetupMeta";
import { PortalApiError, portalFetch } from "../lib/portalApi";

type ChannelRow = {
  connection_id: string;
  channel: string;
  display_name: string;
  status: string;
  configuration: Record<string, string>;
};

function isChannelType(value: string): value is ChannelTypeId {
  return (CHANNEL_TYPES as readonly string[]).includes(value);
}

function isStatus(value: string): value is ChannelStatusId {
  return (CHANNEL_STATUSES as readonly string[]).includes(value);
}

function statusTone(status: string): string {
  switch (status) {
    case "enabled":
      return "text-emerald-300";
    case "configured":
      return "text-sky-300";
    case "disabled":
      return "text-amber-300";
    default:
      return "text-zinc-500";
  }
}

export function ChannelSetupPanel() {
  const [rows, setRows] = useState<ChannelRow[]>([]);
  const [selected, setSelected] = useState<ChannelTypeId | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);
  const [needsProfile, setNeedsProfile] = useState(false);

  const [displayName, setDisplayName] = useState("");
  const [status, setStatus] = useState<ChannelStatusId>("not_configured");
  const [configValues, setConfigValues] = useState<Record<string, string>>({});

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn();
    } catch (err) {
      if (err instanceof PortalApiError) {
        if (err.status === 401) {
          setNeedsAuth(true);
          setError("Sign in required — open First Run to continue.");
        } else if (err.detail === "profile_required") {
          setNeedsProfile(true);
          setError("Complete Business Profile in First Run first.");
        } else {
          setError(err.detail);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("unexpected_error");
      }
    } finally {
      setBusy(false);
    }
  }, []);

  const load = useCallback(async () => {
    await run(async () => {
      const list = await portalFetch<ChannelRow[]>("/portal/chatbot/channels");
      setRows(list);
      setNeedsAuth(false);
      setNeedsProfile(false);
    });
  }, [run]);

  useEffect(() => {
    void load();
  }, [load]);

  const byType = useMemo(() => {
    const map = new Map<ChannelTypeId, ChannelRow | null>();
    for (const type of CHANNEL_TYPES) map.set(type, null);
    for (const row of rows) {
      if (!isChannelType(row.channel)) continue;
      // One primary row per channel type for Setup UX (latest wins if duplicates)
      map.set(row.channel, row);
    }
    return map;
  }, [rows]);

  const readyCount = useMemo(
    () =>
      CHANNEL_TYPES.filter((type) => {
        const row = byType.get(type);
        return row?.status === "enabled" || row?.status === "configured";
      }).length,
    [byType],
  );
  const readinessPct = Math.round((readyCount / CHANNEL_TYPES.length) * 100);

  const current = selected ? byType.get(selected) ?? null : null;
  const meta = selected ? CHANNEL_META[selected] : null;
  const fields = selected ? CHANNEL_CONFIG_FIELDS[selected] : [];

  const openChannel = (type: ChannelTypeId) => {
    const row = byType.get(type) ?? null;
    setSelected(type);
    setDisplayName(row?.display_name || CHANNEL_META[type].label);
    setStatus(
      row && isStatus(row.status) ? row.status : "not_configured",
    );
    const nextConfig: Record<string, string> = {};
    for (const field of CHANNEL_CONFIG_FIELDS[type]) {
      nextConfig[field.key] = row?.configuration?.[field.key] ?? "";
    }
    setConfigValues(nextConfig);
    setNotice(null);
    setError(null);
  };

  const ensureAndSave = () =>
    run(async () => {
      if (!selected) return;
      const configuration: Record<string, string> = {};
      for (const [key, value] of Object.entries(configValues)) {
        const trimmed = value.trim();
        if (trimmed) configuration[key] = trimmed;
      }

      let connectionId = current?.connection_id;
      if (!connectionId) {
        const created = await portalFetch<ChannelRow>("/portal/chatbot/channels", {
          method: "POST",
          body: JSON.stringify({
            channel: selected,
            display_name: displayName.trim() || CHANNEL_META[selected].label,
            status,
            configuration:
              Object.keys(configuration).length > 0 ? configuration : undefined,
          }),
        });
        connectionId = created.connection_id;
        setNotice("Channel registered.");
      } else {
        await portalFetch(`/portal/chatbot/channels/${connectionId}`, {
          method: "PUT",
          body: JSON.stringify({
            display_name: displayName.trim() || CHANNEL_META[selected].label,
            status,
            configuration,
          }),
        });
        setNotice("Channel updated.");
      }
      const list = await portalFetch<ChannelRow[]>("/portal/chatbot/channels");
      setRows(list);
    });

  const applyStatusForType = (type: ChannelTypeId, next: ChannelStatusId) =>
    run(async () => {
      const row = byType.get(type) ?? null;
      if (!row?.connection_id) {
        await portalFetch("/portal/chatbot/channels", {
          method: "POST",
          body: JSON.stringify({
            channel: type,
            display_name: CHANNEL_META[type].label,
            status: next,
          }),
        });
      } else {
        await portalFetch(`/portal/chatbot/channels/${row.connection_id}`, {
          method: "PUT",
          body: JSON.stringify({ status: next }),
        });
      }
      if (selected === type) setStatus(next);
      setNotice(`${CHANNEL_META[type].label}: ${CHANNEL_STATUS_LABEL[next]}`);
      const list = await portalFetch<ChannelRow[]>("/portal/chatbot/channels");
      setRows(list);
    });

  const setQuickStatus = (next: ChannelStatusId) => {
    if (!selected) return;
    void applyStatusForType(selected, next);
  };

  const primaryAction = (row: ChannelRow | null): {
    label: string;
    next?: ChannelStatusId;
  } => {
    if (!row || row.status === "not_configured") {
      return { label: "Configure" };
    }
    if (row.status === "configured" || row.status === "disabled") {
      return { label: "Enable", next: "enabled" };
    }
    return { label: "Disable", next: "disabled" };
  };

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-1 py-2">
      <header className="space-y-2">
        <Badge>Vector · Channels</Badge>
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Channel Setup
        </h1>
        <p className="text-sm text-zinc-400">
          Register where Vector can work. This screen only edits Channel
          Connections — it never talks to Telegram, WhatsApp, or other networks.
        </p>
      </header>

      <section
        className="rounded-2xl border border-white/10 bg-white/[0.03] p-4"
        aria-label="Channel readiness"
      >
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-zinc-500">
              Readiness
            </p>
            <p className="text-2xl font-semibold text-white">{readinessPct}%</p>
            <p className="text-sm text-zinc-500">
              {readyCount} of {CHANNEL_TYPES.length} channels configured or
              enabled
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void load()} disabled={busy}>
              Refresh
            </Button>
            <Link
              href="/projects/chatbot/knowledge"
              className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              Knowledge
            </Link>
            <Link
              href="/projects/chatbot/setup"
              className="inline-flex items-center rounded-xl border border-white/10 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              First Run
            </Link>
          </div>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-black/40">
          <div
            className="h-full rounded-full bg-sky-400/80 transition-all"
            style={{ width: `${readinessPct}%` }}
          />
        </div>
      </section>

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
      {notice ? (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {notice}
        </p>
      ) : null}

      {!selected ? (
        <section aria-label="Channel overview">
          <h2 className="mb-3 text-lg font-medium text-white">Channels</h2>
          <ul className="grid gap-3 sm:grid-cols-2">
            {CHANNEL_TYPES.map((type) => {
              const row = byType.get(type) ?? null;
              const info = CHANNEL_META[type];
              const action = primaryAction(row);
              const statusLabel = row
                ? CHANNEL_STATUS_LABEL[isStatus(row.status) ? row.status : "not_configured"]
                : CHANNEL_STATUS_LABEL.not_configured;
              return (
                <li key={type}>
                  <div className="flex h-full flex-col gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
                    <button
                      type="button"
                      onClick={() => openChannel(type)}
                      className="flex flex-col gap-1 text-left"
                    >
                      <span className="flex items-center justify-between gap-2">
                        <span className="font-medium text-white">{info.label}</span>
                        <span className={`text-xs ${statusTone(row?.status || "not_configured")}`}>
                          {statusLabel}
                        </span>
                      </span>
                      <span className="text-xs text-zinc-500">{info.hint}</span>
                    </button>
                    <div className="mt-auto flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openChannel(type)}
                        disabled={busy}
                      >
                        {action.label === "Configure" ? "Configure" : "Details"}
                      </Button>
                      {action.next ? (
                        <Button
                          size="sm"
                          variant={action.next === "enabled" ? "success" : "ghost"}
                          onClick={() => void applyStatusForType(type, action.next!)}
                          disabled={busy}
                        >
                          {action.label}
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      ) : (
        <section className="space-y-4" aria-label="Channel details">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-medium text-white">{meta?.label}</h2>
              <p className="text-sm text-zinc-500">{meta?.hint}</p>
            </div>
            <Button variant="ghost" onClick={() => setSelected(null)} disabled={busy}>
              ← All channels
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {CHANNEL_STATUSES.map((s) => (
              <Button
                key={s}
                size="sm"
                variant={status === s ? "primary" : "secondary"}
                onClick={() => void setQuickStatus(s)}
                disabled={busy}
              >
                {CHANNEL_STATUS_LABEL[s]}
              </Button>
            ))}
          </div>

          <div className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
            <Field label="Display name">
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={200}
              />
            </Field>
            {fields.map((field) => (
              <Field key={field.key} label={field.label}>
                <Input
                  value={configValues[field.key] ?? ""}
                  onChange={(e) =>
                    setConfigValues((prev) => ({
                      ...prev,
                      [field.key]: e.target.value,
                    }))
                  }
                  placeholder={field.placeholder}
                  maxLength={500}
                />
              </Field>
            ))}
            <p className="text-xs text-zinc-500">
              Stub fields only — secrets, tokens, and OAuth are rejected by the
              API.
            </p>
            <Button onClick={() => void ensureAndSave()} disabled={busy}>
              Save configuration
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
