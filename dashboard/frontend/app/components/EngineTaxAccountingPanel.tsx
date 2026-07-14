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

type HarvestLine = {
  date: string;
  asset_id: string;
  asset_name: string;
  asset_url: string;
  niche: string;
  status: string;
  gross_eur: number;
  commission_eur: number;
  net_after_fees_eur: number;
  tax_reserve_eur: number;
  net_clean_eur: number;
};

type AccountingSummary = {
  tax_settings: TaxSettings;
  totals: Record<string, number>;
  harvest_count: number;
  harvest_lines: HarvestLine[];
  dsgvo_note: string;
  service_label: string;
  operator_ready: boolean;
  operator_trade_name: string;
  export_summary?: {
    entries_count: number;
    fiat_gross_eur: number;
    crypto_gross_eur: number;
    payouts_eur: number;
    platform_balance_eur: number;
    available_for_withdrawal_eur: number;
    format: string;
    note: string;
  };
};

export function EngineTaxAccountingPanel() {
  const [data, setData] = useState<AccountingSummary | null>(null);
  const [settings, setSettings] = useState<TaxSettings | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

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
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/accounting/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setMessage("Налоговые настройки сохранены");
        await refresh();
      } else {
        setMessage("Ошибка сохранения настроек");
      }
    } finally {
      setBusy("");
    }
  }

  function downloadCsv() {
    window.open(`${API}/api/engine/accounting/export.csv`, "_blank");
  }

  function downloadDatev() {
    window.open(`${API}/api/engine/accounting/export.datev.csv`, "_blank");
  }

  function openInvoice(assetId: string) {
    window.open(`${API}/api/engine/accounting/invoice/${assetId}`, "_blank");
  }

  const totals = data?.totals;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-sky-500/30 bg-gradient-to-br from-sky-950/30 via-genesis-panel to-genesis-panel p-6">
        <p className="text-xs uppercase tracking-[0.4em] text-sky-300/90">Tax &amp; Accounting</p>
        <h2 className="mt-2 text-2xl font-bold text-white">Учёт и отчётность для Finanzamt</h2>
        <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
          Fiat (Stripe → банк DE) + crypto ledger (Konto 2742). Finanzamt CSV, DATEV для Steuerberater, Rechnungen B2B.
        </p>
        {data?.export_summary ? (
          <p className="mt-2 text-xs text-sky-200">
            FinancialExportBridge: {data.export_summary.entries_count} проводок · Fiat{" "}
            {formatEur(data.export_summary.fiat_gross_eur)} · Crypto{" "}
            {formatEur(data.export_summary.crypto_gross_eur)} · баланс{" "}
            {formatEur(data.export_summary.platform_balance_eur)}
          </p>
        ) : null}
        {data?.dsgvo_note ? (
          <p className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-950/25 px-3 py-2 text-[11px] text-emerald-100">
            🔒 {data.dsgvo_note}
          </p>
        ) : null}
        {!data?.operator_ready ? (
          <p className="mt-2 text-xs text-amber-200">
            Для полных Rechnungen заполните адрес в legal_entity.json (после Gewerbeanmeldung).
          </p>
        ) : (
          <p className="mt-2 text-xs text-emerald-200">
            Продавец: {data?.operator_trade_name} · данные оператора готовы для счетов.
          </p>
        )}
      </section>

      {totals && (
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Kpi label="Брутто (добыча)" value={formatEur(totals.gross_eur ?? 0)} />
          <Kpi label="Комиссия Stripe" value={formatEur(totals.commission_eur ?? 0)} />
          <Kpi label="После комиссий" value={formatEur(totals.net_after_fees_eur ?? 0)} />
          <Kpi label="Резерв MwSt" value={formatEur(totals.tax_reserve_eur ?? 0)} accent />
          <Kpi label="Чистый доход" value={formatEur(totals.net_clean_eur ?? 0)} accent />
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <section className="genesis-card p-5">
          <h3 className="text-sm font-semibold">Налоговые настройки</h3>
          <p className="mt-1 text-xs text-genesis-muted">
            MwSt (НДС) по умолчанию 19% · Stripe 1,4% + €0,25 за транзакцию.
          </p>
          {settings ? (
            <form onSubmit={saveSettings} className="mt-4 space-y-3">
              <label className="block text-xs">
                <span className="text-genesis-muted">Налоговая ставка MwSt (%)</span>
                <input
                  type="number"
                  min={0}
                  max={50}
                  step={0.1}
                  value={settings.vat_rate_percent}
                  onChange={(e) =>
                    setSettings({ ...settings, vat_rate_percent: parseFloat(e.target.value) || 0 })
                  }
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
              </label>
              <label className="block text-xs">
                <span className="text-genesis-muted">Комиссия Stripe (%)</span>
                <input
                  type="number"
                  min={0}
                  max={10}
                  step={0.1}
                  value={settings.stripe_fee_percent}
                  onChange={(e) =>
                    setSettings({ ...settings, stripe_fee_percent: parseFloat(e.target.value) || 0 })
                  }
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
              </label>
              <label className="block text-xs">
                <span className="text-genesis-muted">Фикс. комиссия Stripe (€)</span>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={settings.stripe_fee_fixed_eur}
                  onChange={(e) =>
                    setSettings({ ...settings, stripe_fee_fixed_eur: parseFloat(e.target.value) || 0 })
                  }
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
              </label>
              <label className="block text-xs">
                <span className="text-genesis-muted">Услуга (Kleingewerbe / Rechnung)</span>
                <input
                  value={settings.service_label}
                  onChange={(e) => setSettings({ ...settings, service_label: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
              </label>
              <button
                type="submit"
                disabled={busy === "save"}
                className="w-full rounded-xl bg-sky-600 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy === "save" ? "Сохранение…" : "Сохранить настройки"}
              </button>
            </form>
          ) : null}
        </section>

        <section className="genesis-card p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">Журнал добычи · {data?.harvest_count ?? 0} записей</h3>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={downloadCsv}
                className="rounded-lg border border-sky-500/40 bg-sky-950/30 px-3 py-1.5 text-xs text-sky-100 hover:bg-sky-900/40"
              >
                ⬇ CSV Finanzamt
              </button>
              <button
                type="button"
                onClick={downloadDatev}
                className="rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-3 py-1.5 text-xs text-emerald-100 hover:bg-emerald-900/40"
              >
                ⬇ DATEV / Lexoffice
              </button>
            </div>
          </div>
          <p className="mt-1 text-xs text-genesis-muted">
            Формат DE: разделитель «;», запятая как десятичный разделитель. Печать → PDF.
          </p>
          {!data?.harvest_lines.length ? (
            <p className="mt-4 text-sm text-genesis-muted">Пока нет монетизированных активов с доходом.</p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-[11px]">
                <thead>
                  <tr className="border-b border-white/10 text-genesis-muted">
                    <th className="py-2 pr-2">Дата</th>
                    <th className="py-2 pr-2">Актив</th>
                    <th className="py-2 pr-2 text-right">Брутто</th>
                    <th className="py-2 pr-2 text-right">Комиссия</th>
                    <th className="py-2 pr-2 text-right">Чистый</th>
                    <th className="py-2">Rechnung</th>
                  </tr>
                </thead>
                <tbody>
                  {data.harvest_lines.map((line) => (
                    <tr key={line.asset_id} className="border-b border-white/5">
                      <td className="py-2 pr-2 tabular-nums">{line.date || "—"}</td>
                      <td className="py-2 pr-2">
                        <span className="font-medium text-white">{line.asset_name || "—"}</span>
                        {line.asset_url ? (
                          <a
                            href={line.asset_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block text-[10px] text-emerald-300/80 hover:underline"
                          >
                            {line.asset_url}
                          </a>
                        ) : null}
                      </td>
                      <td className="py-2 pr-2 text-right tabular-nums">{formatEur(line.gross_eur)}</td>
                      <td className="py-2 pr-2 text-right tabular-nums text-amber-200">
                        {formatEur(line.commission_eur)}
                      </td>
                      <td className="py-2 pr-2 text-right tabular-nums text-emerald-300">
                        {formatEur(line.net_clean_eur)}
                      </td>
                      <td className="py-2">
                        <button
                          type="button"
                          onClick={() => openInvoice(line.asset_id)}
                          className="rounded border border-white/15 px-2 py-0.5 text-[10px] hover:bg-white/5"
                        >
                          PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {message ? (
        <p className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-genesis-muted">{message}</p>
      ) : null}
    </div>
  );
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        accent ? "border-sky-500/35 bg-sky-950/20" : "border-genesis-border-subtle bg-genesis-bg/40"
      }`}
    >
      <p className={`text-xl font-bold tabular-nums ${accent ? "text-sky-200" : "text-white"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
