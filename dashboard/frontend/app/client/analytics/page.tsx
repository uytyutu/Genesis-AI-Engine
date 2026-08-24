"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import {
  metricsForPanel,
  panelStateLabel,
  type AnalyticsOverview,
  type AnalyticsPanel,
  type MetricContract,
} from "../../lib/bccAnalyticsComposition";
import { publicApiBase } from "../../lib/publicApiBase";
import { BccPanel, BccSectionHeader } from "../../lib/clientUi";

const API = publicApiBase();

function MetricBlock({ metric }: { metric: MetricContract }) {
  const last = metric.points[metric.points.length - 1];
  const value =
    last == null
      ? "—"
      : metric.unit === "eur"
        ? `${last.v.toLocaleString("de-DE", { maximumFractionDigits: 2 })} €`
        : String(last.v);
  return (
    <div className="rounded-xl border border-white/10 bg-black/30 px-3 py-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
        {metric.label}
      </p>
      <p className="mt-1 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-[10px] text-zinc-600">
        Quelle · {metric.source_id} · Stand {metric.as_of.slice(0, 10)}
      </p>
      {/* Chart-ready series preserved for future graphs — no invented points */}
      {metric.points.length > 1 ? (
        <p className="mt-2 text-[10px] text-zinc-500">
          Serie: {metric.points.length} Punkte (für Grafik vorbereitet)
        </p>
      ) : null}
    </div>
  );
}

function PanelCard({
  overview,
  panel,
}: {
  overview: AnalyticsOverview;
  panel: AnalyticsPanel;
}) {
  const metrics = metricsForPanel(overview, panel);
  return (
    <BccPanel className="flex h-full flex-col p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-white">{panel.title}</p>
        <span className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
          {panelStateLabel(panel.state)}
        </span>
      </div>
      {panel.state === "coming_soon" ? (
        <p className="mt-3 text-sm text-zinc-500">Coming Soon — kein Fake-KPI.</p>
      ) : panel.state === "not_connected" ? (
        <p className="mt-3 text-sm text-zinc-500">
          Quelle nicht verbunden — keine Besucher-/Seiten-Zahlen.
        </p>
      ) : panel.state === "connected_no_data" ? (
        <p className="mt-3 text-sm text-zinc-500">
          Analytics verbunden · Noch keine Daten verfügbar.
        </p>
      ) : metrics.length === 0 ? (
        <p className="mt-3 text-sm text-zinc-500">Keine Kennzahlen für dieses Panel.</p>
      ) : (
        <div className="mt-3 grid gap-2">
          {metrics.map((m) => (
            <MetricBlock key={m.metric_id} metric={m} />
          ))}
        </div>
      )}
    </BccPanel>
  );
}

export default function ClientAnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectMsg, setConnectMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      setError("auth_required");
      return;
    }
    setError(null);
    try {
      const res = await fetch(`${API}/api/client/analytics/overview?period=30d`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = (await res.json().catch(() => ({}))) as AnalyticsOverview;
      if (!res.ok) {
        setError(String((body as { detail?: string }).detail || res.status));
        setData(null);
        return;
      }
      setData(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onConnect() {
    setBusy(true);
    setConnectMsg(null);
    try {
      const res = await fetch(`${API}/api/client/analytics/connect`, {
        method: "POST",
        headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
        body: "{}",
      });
      const body = await res.json().catch(() => ({}));
      setConnectMsg(
        String(body.message || body.detail || "Externe Analytics noch nicht verfügbar."),
      );
    } catch (e) {
      setConnectMsg(e instanceof Error ? e.message : "connect_failed");
    } finally {
      setBusy(false);
    }
  }

  const copy = data?.copy;
  const state = data?.analytics_state || "not_connected";

  return (
    <ClientWorkspaceShell
      title="Analytics"
      subtitle="Nur echte Quellen — keine erfundenen Besucher oder Umsätze."
    >
      {error ? (
        <p className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      <BccPanel className="mb-6 border-dashed border-violet-400/30 bg-violet-500/[0.06] p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300/90">
          Status · {panelStateLabel(state)}
        </p>
        <h2 className="mt-3 text-xl font-semibold text-white">
          {copy?.title || "Analytics noch nicht verbunden"}
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
          {copy?.body ||
            "Verbinde Analytics, um echte Besucherdaten zu sehen."}
        </p>
        {copy?.hint ? (
          <p className="mt-2 max-w-2xl text-xs text-zinc-600">{copy.hint}</p>
        ) : null}
        <div className="mt-6 flex flex-wrap gap-3">
          {state === "not_connected" ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void onConnect()}
              className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50"
            >
              {busy ? "…" : "Analytics hinzufügen"}
            </button>
          ) : null}
          <Link
            href="/client/products"
            className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Meine Produkte
          </Link>
        </div>
        {connectMsg ? (
          <p className="mt-4 rounded-lg border border-amber-400/25 bg-amber-500/10 px-3 py-2 text-sm text-amber-100/90">
            {connectMsg}
          </p>
        ) : null}
      </BccPanel>

      {data ? (
        <>
          <BccSectionHeader title="Quellen" />
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {(data.sources || []).map((s) => (
              <li
                key={s.source_id}
                className="rounded-xl border border-white/8 bg-black/25 px-3 py-3 text-sm"
              >
                <span className="font-medium text-zinc-200">{s.label}</span>
                <span className="ml-2 text-[10px] uppercase tracking-wide text-zinc-500">
                  {panelStateLabel(s.status)}
                </span>
                <p className="mt-1 text-xs text-zinc-600">{s.reason}</p>
              </li>
            ))}
          </ul>

          <div className="mt-8">
            <BccSectionHeader title="Product-aware Panels" />
            <ul className="mt-3 grid gap-3 sm:grid-cols-2">
              {(data.panels || []).map((panel) => (
                <li key={panel.panel_id}>
                  <PanelCard overview={data} panel={panel} />
                </li>
              ))}
            </ul>
          </div>

          {(data.metrics || []).length > 0 ? (
            <div className="mt-8">
              <BccSectionHeader title="Alle echten Kennzahlen" />
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {data.metrics.map((m) => (
                  <MetricBlock key={m.metric_id} metric={m} />
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : !error ? (
        <p className="text-sm text-zinc-500">Analytics wird geladen…</p>
      ) : null}
    </ClientWorkspaceShell>
  );
}
