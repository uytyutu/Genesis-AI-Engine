"use client";

import { useCallback, useEffect, useState } from "react";
import { getBackendApiBase } from "../lib/backendApiBase";

const API = getBackendApiBase();

type HumanSummary = {
  budget?: string;
  automation?: string;
  toloka?: string;
  ai_api?: string;
  estimated?: string;
  expected_profit?: string;
  success_probability?: string;
  opportunity_score?: string;
};

type Opportunity = {
  id: string;
  source?: string;
  title?: string;
  status?: string;
  url?: string;
  expected_revenue?: number;
  expected_cost?: number;
  expected_profit?: number;
  automation_percent?: number;
  success_probability?: number;
  opportunity_score?: number;
  economics?: { human_summary?: HumanSummary; decision?: string };
  proposal?: { text?: string; copy_only?: boolean };
};

type Reality = {
  real_revenue_eur?: number;
  real_paid_orders?: number;
  pipeline_value_eur?: number;
  expected_profit_eur?: number;
  toloka_balance_usd?: number | null;
  active_opportunities?: number;
};

type Panel = {
  ok?: boolean;
  rule_ru?: string;
  first_money_ru?: string;
  reality?: Reality;
  top?: Opportunity[];
  pipeline?: Record<string, number>;
};

export function MoneyHunterPanel({ compact }: { compact?: boolean }) {
  const [panel, setPanel] = useState<Panel | null>(null);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [budget, setBudget] = useState("100");
  const [source, setSource] = useState("manual");
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [pendingId, setPendingId] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/farm/money-hunter`);
      const json = (await res.json()) as Panel;
      setPanel(json);
      setMsg("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Money Hunter load failed");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function importJob() {
    setBusy("import");
    setMsg("");
    try {
      const b = Number(budget) || 0;
      const res = await fetch(`${API}/api/farm/opportunities/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          title,
          description,
          url,
          budget_min: b,
          budget_max: b,
          currency: "EUR",
          first_money_mode: true,
        }),
      });
      const data = await res.json();
      if (!data?.ok) setMsg(String(data?.error || "import failed"));
      else {
        setMsg(
          data.deduped
            ? `Duplicate — ${data.opportunity?.id}`
            : `Imported ${data.opportunity?.id} · ${data.opportunity?.status}`,
        );
        setTitle("");
        setDescription("");
      }
      await refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "import failed");
    } finally {
      setBusy("");
    }
  }

  async function approve(id: string, confirm: boolean) {
    setBusy(`approve:${id}`);
    setMsg("");
    try {
      const q = new URLSearchParams({ confirm: confirm ? "true" : "false" });
      const res = await fetch(
        `${API}/api/farm/opportunities/${encodeURIComponent(id)}/approve?${q}`,
        { method: "POST" },
      );
      const data = await res.json();
      if (data?.requires_confirm) {
        setPendingId(id);
        setPreview(data.approval_preview || null);
        setMsg("Confirm spend limits below, then CONFIRM APPROVE.");
      } else if (!data?.ok) {
        setMsg(String(data?.error || "approve failed"));
      } else {
        setPreview(null);
        setPendingId("");
        setMsg(`APPROVED ${id}`);
        await refresh();
      }
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "approve failed");
    } finally {
      setBusy("");
    }
  }

  async function reject(id: string) {
    setBusy(`reject:${id}`);
    try {
      await fetch(
        `${API}/api/farm/opportunities/${encodeURIComponent(id)}/reject`,
        { method: "POST" },
      );
      await refresh();
    } finally {
      setBusy("");
    }
  }

  const reality = panel?.reality;
  const top = panel?.top || [];

  return (
    <section className="rounded-2xl border border-amber-500/35 bg-amber-950/15 p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-amber-100">Money Hunter</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            {panel?.rule_ru ||
              "REAL ≠ pipeline. Paste job → analyze → approve → execute."}
          </p>
          <p className="mt-1 text-[11px] text-amber-100/80">{panel?.first_money_ru}</p>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded-lg border border-white/15 px-2 py-1 text-xs text-genesis-muted"
        >
          Refresh
        </button>
      </div>

      <div className={`mt-4 grid gap-2 ${compact ? "grid-cols-2" : "grid-cols-2 md:grid-cols-4"}`}>
        <Stat label="REAL REVENUE" value={`€${reality?.real_revenue_eur ?? 0}`} hot />
        <Stat label="Paid orders" value={String(reality?.real_paid_orders ?? 0)} />
        <Stat label="Pipeline (est.)" value={`€${reality?.pipeline_value_eur ?? 0}`} />
        <Stat label="Expected profit" value={`€${reality?.expected_profit_eur ?? 0}`} />
      </div>

      <div className="mt-4 rounded-xl border border-white/10 bg-black/25 p-3">
        <p className="text-sm font-medium text-white">Manual import</p>
        <p className="mt-1 text-[11px] text-genesis-muted">
          Copy job from Upwork / Fiverr / Malt / freelance.de → paste here. No scraping.
        </p>
        <div className="mt-2 grid gap-2 md:grid-cols-2">
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
          >
            <option value="manual">Universal manual</option>
            <option value="upwork_manual">Upwork manual</option>
            <option value="fiverr_manual">Fiverr manual</option>
            <option value="malt_manual">Malt manual</option>
            <option value="freelance_de_manual">freelance.de manual</option>
          </select>
          <input
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            placeholder="Budget EUR"
            className="rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
          />
        </div>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
          className="mt-2 w-full rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
        />
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="URL (optional)"
          className="mt-2 w-full rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Full job text"
          rows={compact ? 3 : 5}
          className="mt-2 w-full rounded-lg border border-white/15 bg-black/40 px-2 py-1.5 text-xs text-white"
        />
        <button
          type="button"
          disabled={!!busy || (!title.trim() && !description.trim())}
          onClick={() => void importJob()}
          className="mt-2 rounded-lg border border-amber-400/40 bg-amber-900/40 px-3 py-1.5 text-xs font-medium text-amber-50 disabled:opacity-40"
        >
          {busy === "import" ? "Analyzing…" : "Import & Analyze"}
        </button>
      </div>

      {preview && pendingId ? (
        <div className="mt-3 rounded-xl border border-rose-400/40 bg-rose-950/30 p-3 text-xs text-rose-50">
          <p className="font-semibold">You are approving {pendingId}</p>
          <ul className="mt-2 space-y-1 text-rose-100/90">
            <li>Expected revenue: €{String(preview.expected_revenue ?? "—")}</li>
            <li>Maximum cost: €{String(preview.maximum_cost ?? "—")}</li>
            <li>Toloka: €{String(preview.toloka_cost ?? "—")}</li>
            <li>AI: €{String(preview.ai_cost ?? "—")}</li>
            <li>Other: €{String(preview.other ?? "—")}</li>
            <li>Expected profit: €{String(preview.expected_profit ?? "—")}</li>
          </ul>
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={() => void approve(pendingId, true)}
              className="rounded-lg border border-emerald-400/50 bg-emerald-900/40 px-3 py-1 text-emerald-50"
            >
              CONFIRM
            </button>
            <button
              type="button"
              onClick={() => {
                setPreview(null);
                setPendingId("");
              }}
              className="rounded-lg border border-white/20 px-3 py-1 text-white/80"
            >
              CANCEL
            </button>
          </div>
        </div>
      ) : null}

      {msg ? <p className="mt-2 text-xs text-amber-100/90">{msg}</p> : null}

      <div className="mt-4 space-y-3">
        {top.length === 0 ? (
          <p className="text-xs text-genesis-muted">No opportunities yet — paste a real job above.</p>
        ) : (
          top.map((o) => {
            const hs = o.economics?.human_summary;
            const high = (o.opportunity_score || 0) >= 70;
            return (
              <article
                key={o.id}
                className="rounded-xl border border-white/10 bg-black/30 p-3 text-xs"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-[10px] uppercase tracking-wide text-amber-200/80">
                      {high ? "High value opportunity" : "Opportunity"} · {o.source}
                    </p>
                    <p className="mt-1 text-sm font-medium text-white">{o.title}</p>
                    <p className="mt-1 text-genesis-muted">Status: {o.status}</p>
                  </div>
                  <p className="text-amber-100">{hs?.opportunity_score || `${o.opportunity_score}/100`}</p>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-1 text-white/85 md:grid-cols-4">
                  <span>Budget: {hs?.budget || `€${o.expected_revenue}`}</span>
                  <span>Automation: {hs?.automation || `${o.automation_percent}%`}</span>
                  <span>Toloka: {hs?.toloka}</span>
                  <span>AI: {hs?.ai_api}</span>
                  <span>Est: {hs?.estimated}</span>
                  <span>Profit: {hs?.expected_profit}</span>
                  <span>Success: {hs?.success_probability}</span>
                  <span>Decision: {o.economics?.decision}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {o.url ? (
                    <a
                      href={o.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded border border-white/20 px-2 py-1 text-sky-200"
                    >
                      VIEW
                    </a>
                  ) : null}
                  {o.status === "PENDING_APPROVAL" || o.status === "QUALIFIED" ? (
                    <>
                      <button
                        type="button"
                        disabled={!!busy}
                        onClick={() => void approve(o.id, false)}
                        className="rounded border border-emerald-400/40 px-2 py-1 text-emerald-100"
                      >
                        APPROVE
                      </button>
                      <button
                        type="button"
                        disabled={!!busy}
                        onClick={() => void reject(o.id)}
                        className="rounded border border-rose-400/40 px-2 py-1 text-rose-100"
                      >
                        REJECT
                      </button>
                    </>
                  ) : null}
                  {o.proposal?.text ? (
                    <button
                      type="button"
                      onClick={() => {
                        void navigator.clipboard.writeText(o.proposal?.text || "");
                        setMsg("Proposal copied — not auto-sent.");
                      }}
                      className="rounded border border-white/20 px-2 py-1 text-white/90"
                    >
                      COPY PROPOSAL
                    </button>
                  ) : null}
                </div>
              </article>
            );
          })
        )}
      </div>
    </section>
  );
}

function Stat({
  label,
  value,
  hot,
}: {
  label: string;
  value: string;
  hot?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border px-2 py-2 ${
        hot ? "border-emerald-400/40 bg-emerald-950/30" : "border-white/10 bg-black/20"
      }`}
    >
      <p className="text-[10px] uppercase tracking-wide text-genesis-muted">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${hot ? "text-emerald-100" : "text-white"}`}>
        {value}
      </p>
    </div>
  );
}
