"use client";

import { useCallback, useEffect, useState } from "react";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type TaxSettings = {
  vat_rate_percent: number;
  stripe_fee_percent: number;
  stripe_fee_fixed_eur: number;
  service_label: string;
};

type PotentialRevenue = {
  potential_revenue_eur: number;
  pipeline_potential_eur: number;
  hunter_potential_eur: number;
  micro_potential_eur: number;
  dust_potential_eur: number;
  active_leads: number;
  high_score_leads: number;
  disclaimer: string;
};

type AccountingSummary = {
  system_mode?: string;
  financial_docs_enabled?: boolean;
  tax_settings: TaxSettings;
  totals: Record<string, number>;
  potential_revenue?: PotentialRevenue;
  harvest_count: number;
  harvest_lines: unknown[];
  dsgvo_note: string;
  sandbox_note?: string;
  export_summary?: Record<string, unknown>;
};

export function EngineTaxAccountingPanel() {
  const [data, setData] = useState<AccountingSummary | null>(null);
  const [settings, setSettings] = useState<TaxSettings | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const isSandbox = data?.system_mode !== "live";

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engine/accounting`);
      if (res.ok) {
        const body: AccountingSummary = await res.json();
        setData(body);
        setSettings(body.tax_settings);
      }
    } catch {
      setMessage("Не удалось загрузить учёт. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setBusy("save");
    try {
      const res = await fetch(`${API}/api/engine/accounting/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setMessage("Налоговые настройки сохранены");
        await refresh();
      }
    } finally {
      setBusy("");
    }
  }

  function blockedExport(label: string) {
    if (isSandbox) {
      setMessage(`Sandbox: ${label} отключён до ACTIVATE BUSINESS`);
      return;
    }
  }

  const potential = data?.potential_revenue;

  if (isSandbox) {
    return (
      <div className="space-y-6">
        <section className="rounded-2xl border border-amber-500/40 bg-amber-950/25 p-6">
          <p className="text-xs uppercase tracking-widest text-amber-300">Sandbox · Tax заблокирован</p>
          <h2 className="mt-2 text-2xl font-bold text-white">Potential Revenue (не Finanzamt)</h2>
          <p className="mt-2 text-sm text-genesis-muted">{data?.sandbox_note ?? data?.dsgvo_note}</p>
          {potential ? (
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <Kpi label="Потенциал всего" value={formatEur(potential.potential_revenue_eur)} accent />
              <Kpi label="Воронка лидов" value={formatEur(potential.pipeline_potential_eur)} />
              <Kpi label="Hunter потенциал" value={formatEur(potential.hunter_potential_eur)} />
            </div>
          ) : null}
          <p className="mt-4 text-xs text-amber-200">{potential?.disclaimer}</p>
          <p className="mt-4 text-sm text-white">
            Лидов: {potential?.active_leads ?? 0} · сильных (score≥45): {potential?.high_score_leads ?? 0}
          </p>
          <div className="mt-6 flex flex-wrap gap-2 opacity-50">
            <button type="button" disabled className="rounded-lg border px-3 py-1.5 text-xs">
              CSV Finanzamt (Live)
            </button>
            <button type="button" disabled className="rounded-lg border px-3 py-1.5 text-xs">
              DATEV (Live)
            </button>
            <button type="button" disabled className="rounded-lg border px-3 py-1.5 text-xs">
              Rechnung PDF (Live)
            </button>
          </div>
          <p className="mt-3 text-xs text-genesis-muted">
            Нажмите <strong>ACTIVATE BUSINESS</strong> на вкладке Движок после Gewerbeanmeldung.
          </p>
        </section>
        {message ? <p className="text-xs text-genesis-muted">{message}</p> : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-sky-500/30 bg-gradient-to-br from-sky-950/30 via-genesis-panel to-genesis-panel p-6">
        <p className="text-xs uppercase tracking-[0.4em] text-sky-300/90">Tax &amp; Accounting · Live</p>
        <h2 className="mt-2 text-2xl font-bold text-white">Учёт и отчётность для Finanzamt</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Fiat (Stripe → банк DE) + crypto ledger (Konto 2742). Finanzamt CSV, DATEV для Steuerberater, Rechnungen B2B.
        </p>
        {data?.export_summary && "entries_count" in data.export_summary ? (
          <p className="mt-2 text-xs text-sky-200">
            FinancialExportBridge: {(data.export_summary as { entries_count: number }).entries_count} проводок
          </p>
        ) : null}
        {data?.dsgvo_note ? (
          <p className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-950/25 px-3 py-2 text-[11px] text-emerald-100">
            🔒 {data.dsgvo_note}
          </p>
        ) : null}
      </section>

      {data?.totals ? (
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Kpi label="Брутто (добыча)" value={formatEur(data.totals.gross_eur ?? 0)} />
          <Kpi label="Комиссия Stripe" value={formatEur(data.totals.commission_eur ?? 0)} />
          <Kpi label="После комиссий" value={formatEur(data.totals.net_after_fees_eur ?? 0)} />
          <Kpi label="Резерв MwSt" value={formatEur(data.totals.tax_reserve_eur ?? 0)} accent />
          <Kpi label="Чистый доход" value={formatEur(data.totals.net_clean_eur ?? 0)} accent />
        </section>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <section className="genesis-card p-5">
          <h3 className="text-sm font-semibold">Налоговые настройки</h3>
          {settings ? (
            <form onSubmit={saveSettings} className="mt-4 space-y-3">
              <label className="block text-xs">
                <span className="text-genesis-muted">MwSt (%)</span>
                <input
                  type="number"
                  value={settings.vat_rate_percent}
                  onChange={(e) =>
                    setSettings({ ...settings, vat_rate_percent: parseFloat(e.target.value) || 0 })
                  }
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
              </label>
              <button type="submit" disabled={busy === "save"} className="w-full rounded-xl bg-sky-600 py-2.5 text-sm font-semibold text-white">
                {busy === "save" ? "Сохранение…" : "Сохранить"}
              </button>
            </form>
          ) : null}
        </section>
        <section className="genesis-card p-5">
          <div className="flex gap-2">
            <button type="button" onClick={() => window.open(`${API}/api/engine/accounting/export.csv`, "_blank")} className="rounded-lg border px-3 py-1.5 text-xs">
              CSV Finanzamt
            </button>
            <button type="button" onClick={() => window.open(`${API}/api/engine/accounting/export.datev.csv`, "_blank")} className="rounded-lg border px-3 py-1.5 text-xs">
              DATEV
            </button>
          </div>
          <p className="mt-4 text-sm text-genesis-muted">{data?.harvest_count ?? 0} записей с реальным доходом</p>
        </section>
      </div>
      {message ? <p className="text-xs text-genesis-muted">{message}</p> : null}
    </div>
  );
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={`rounded-xl border p-4 ${accent ? "border-emerald-500/35 bg-emerald-950/20" : "border-white/10"}`}>
      <p className={`text-xl font-bold tabular-nums ${accent ? "text-emerald-300" : "text-white"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
