"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getBackendApiBase } from "../lib/backendApiBase";

const API = getBackendApiBase();

type Candidate = {
  id: string;
  name?: string;
  category?: string;
  status?: string;
  total_score?: number;
  last_error?: string;
  rapidapi_api_id?: string;
  acquisition?: { ceo_action?: string[] } | null;
};

type StatusPayload = {
  auto_publish?: boolean;
  portfolio?: Record<string, number>;
  revenue?: Record<string, number | string>;
  credentials?: { rapidapi_account?: boolean; publish_token?: boolean };
  payout_path_ru?: string;
  money_rule_ru?: string;
  ceo_action?: string[];
  requires_ceo_action?: boolean;
  paypal_payout_confirmed?: boolean;
  public_api?: { ok?: boolean; base?: string; detail?: string };
  best_candidate?: { id?: string; name?: string; status?: string; total_score?: number } | null;
  markets?: {
    countries_total?: number;
    live?: number;
    ready?: number;
    planned?: number;
    blocked?: number;
    data_available?: number;
  };
  market_matrix?: Array<{
    country?: string;
    name?: string;
    postal?: boolean;
    city?: boolean;
    status?: string;
  }>;
};

export function ApiFarmPanel({ compact }: { compact?: boolean }) {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [s, c] = await Promise.all([
        fetch(`${API}/api/farm/rapidapi/status`).then((r) => r.json()),
        fetch(`${API}/api/farm/rapidapi/candidates?top=20`).then((r) => r.json()),
      ]);
      setStatus(s);
      setCandidates(Array.isArray(c?.candidates) ? c.candidates : []);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "API Farm load failed");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function run(action: string, candidateId = "") {
    setBusy(action);
    setMsg("");
    try {
      const q = new URLSearchParams({ action, max_steps: "12" });
      if (candidateId) q.set("candidate_id", candidateId);
      const res = await fetch(`${API}/api/farm/rapidapi/run?${q}`, { method: "POST" });
      const data = await res.json();
      if (!data?.ok && data?.error) setMsg(String(data.error));
      else if (data?.requires_ceo_action)
        setMsg(
          Array.isArray(data.requires_ceo_action)
            ? data.requires_ceo_action.join(" · ")
            : String(data.detail || data.requires_ceo_action),
        );
      else setMsg(`${action}: ok`);
      await refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "run failed");
    } finally {
      setBusy("");
    }
  }

  async function approve(id: string) {
    setBusy(`approve:${id}`);
    await fetch(`${API}/api/farm/rapidapi/approve/${encodeURIComponent(id)}`, {
      method: "POST",
    });
    await refresh();
    setBusy("");
  }

  async function publish(id: string) {
    setBusy(`publish:${id}`);
    const res = await fetch(`${API}/api/farm/rapidapi/publish/${encodeURIComponent(id)}`, {
      method: "POST",
    });
    const data = await res.json();
    if (data?.ok) {
      setMsg(
        `Published apiId=${data.api_id || "?"} · ${
          Array.isArray(data.requires_ceo_action)
            ? data.requires_ceo_action[0]
            : "check Hub pricing / PayPal"
        }`,
      );
    } else {
      setMsg(String(data?.detail || data?.error || "publish blocked"));
    }
    await refresh();
    setBusy("");
  }

  const port = status?.portfolio || {};
  const rev = status?.revenue || {};
  const ceo = status?.ceo_action || [];

  return (
    <section className="rounded-2xl border border-violet-500/30 bg-violet-950/15 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-violet-100">API Farm · Revenue</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            {status?.money_rule_ru ?? "Actual = PAID_OUT only"} ·{" "}
            {status?.payout_path_ru ?? "RapidAPI → PayPal"} · AUTO_PUBLISH=
            {String(status?.auto_publish ?? false)}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Link href="/farm/rapidapi" className="text-xs text-emerald-300 hover:underline">
            Full page →
          </Link>
          <Link href="/business/api-markets" className="text-xs text-violet-300 hover:underline">
            Markets →
          </Link>
        </div>
      </div>

      {ceo.length ? (
        <div className="mt-3 rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-100">
          <p className="font-semibold">CEO ACTION</p>
          <ul className="mt-1 list-disc space-y-0.5 pl-4">
            {ceo.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {status?.best_candidate ? (
        <p className="mt-3 text-xs text-violet-100/90">
          Best track: <span className="font-medium">{status.best_candidate.name}</span> ·{" "}
          {status.best_candidate.status} · score{" "}
          {Number(status.best_candidate.total_score ?? 0).toFixed(1)}
        </p>
      ) : null}

      {status?.markets ? (
        <div className="mt-3 rounded-lg border border-violet-500/25 bg-black/20 px-3 py-2 text-xs text-violet-100/90">
          <p className="font-semibold text-violet-50">Global Market Coverage</p>
          <p className="mt-1">
            Countries {status.markets.countries_total ?? "—"} · LIVE {status.markets.live ?? 0} ·
            READY {status.markets.ready ?? 0} · PLANNED {status.markets.planned ?? 0}
            {(status.markets.blocked ?? 0) > 0 ? ` · BLOCKED ${status.markets.blocked}` : ""}
          </p>
          <p className="mt-1 text-[11px] text-genesis-muted">
            LIVE only with verified commercial datasets — no fake cities/PLZ.
          </p>
          {!compact && status.market_matrix?.length ? (
            <ul className="mt-2 grid gap-0.5 sm:grid-cols-2">
              {status.market_matrix.slice(0, 13).map((m) => (
                <li key={m.country || m.name}>
                  {m.country} {m.name} · {m.status}
                  {m.postal ? " · postal" : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <div className={`mt-4 grid gap-2 ${compact ? "grid-cols-3" : "grid-cols-3 sm:grid-cols-6"}`}>
        {(
          [
            ["Candidates", port.candidates],
            ["Building", port.building],
            ["Testing", port.testing],
            ["Ready", port.ready],
            ["Published", port.published],
            ["Active", port.active],
          ] as const
        ).map(([label, val]) => (
          <div key={label} className="rounded-lg border border-white/10 bg-black/20 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-genesis-muted">{label}</p>
            <p className="mt-1 font-semibold tabular-nums text-white">{Number(val ?? 0)}</p>
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-genesis-muted">
        <span>Gross {Number(rev.gross_revenue ?? 0).toFixed(2)}</span>
        <span>Fee {Number(rev.marketplace_fee ?? 0).toFixed(2)}</span>
        <span>Net {Number(rev.net_earned ?? 0).toFixed(2)}</span>
        <span>Pending {Number(rev.pending_payout ?? 0).toFixed(2)}</span>
        <span className="text-emerald-200">Actual {Number(rev.actual_revenue ?? 0).toFixed(2)}</span>
        <span>
          PayPal{" "}
          {status?.paypal_payout_confirmed ? "connected flag" : "CEO ACTION"}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!!busy}
          onClick={() => void run("first_api")}
          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
        >
          {busy === "first_api" ? "…" : "Довести первый API"}
        </button>
        <button
          type="button"
          disabled={!!busy}
          onClick={() => void run("discover")}
          className="rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
        >
          {busy === "discover" ? "…" : "Research"}
        </button>
        <button
          type="button"
          disabled={!!busy}
          onClick={() => void run("burst")}
          className="rounded-lg border border-white/20 px-3 py-1.5 text-xs text-white disabled:opacity-50"
        >
          Run queue
        </button>
        <button
          type="button"
          disabled={!!busy}
          onClick={() => void refresh()}
          className="rounded-lg border border-white/15 px-3 py-1.5 text-xs text-genesis-muted"
        >
          Refresh
        </button>
      </div>

      {msg ? <p className="mt-2 text-xs text-amber-100/90">{msg}</p> : null}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-xs">
          <thead className="text-genesis-muted">
            <tr>
              <th className="py-1 pr-2">API</th>
              <th className="py-1 pr-2">Status</th>
              <th className="py-1 pr-2">Score</th>
              <th className="py-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {candidates.slice(0, compact ? 5 : 12).map((c) => (
              <tr key={c.id} className="border-t border-white/10 text-white/90">
                <td className="py-2 pr-2">
                  <p className="font-medium">{c.name}</p>
                  <p className="text-[10px] text-genesis-muted">
                    {c.category}
                    {c.rapidapi_api_id ? ` · apiId ${c.rapidapi_api_id}` : ""}
                  </p>
                </td>
                <td className="py-2 pr-2">{c.status}</td>
                <td className="py-2 pr-2 tabular-nums">{Number(c.total_score ?? 0).toFixed(1)}</td>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1">
                    <button
                      type="button"
                      className="rounded border border-white/15 px-1.5 py-0.5"
                      onClick={() => void run("build", c.id)}
                    >
                      Build
                    </button>
                    <button
                      type="button"
                      className="rounded border border-white/15 px-1.5 py-0.5"
                      onClick={() => void run("quality_gate", c.id)}
                    >
                      Gate
                    </button>
                    <button
                      type="button"
                      className="rounded border border-emerald-500/40 px-1.5 py-0.5 text-emerald-200"
                      onClick={() => void approve(c.id)}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      className="rounded border border-violet-400/40 px-1.5 py-0.5 text-violet-100"
                      onClick={() => void publish(c.id)}
                    >
                      Publish
                    </button>
                    {c.rapidapi_api_id ? (
                      <button
                        type="button"
                        className="rounded border border-sky-400/40 px-1.5 py-0.5 text-sky-100"
                        onClick={() => void run("acquire", c.id)}
                      >
                        Acquire
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
            {!candidates.length ? (
              <tr>
                <td colSpan={4} className="py-3 text-genesis-muted">
                  No candidates — press «Довести первый API».
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
