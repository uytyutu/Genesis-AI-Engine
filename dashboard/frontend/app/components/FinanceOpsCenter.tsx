"use client";

import { useCallback, useEffect, useState } from "react";
import { formatEur } from "../lib/formatEur";
import { GenesisCard } from "./GenesisCard";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type OpsRow = {
  order_id?: string;
  date?: string;
  amount_eur?: number;
  label?: string;
  vendor?: string;
  category?: string;
  kind?: string;
  has_pdf?: boolean;
  id?: string;
};

type OpsAlert = {
  id?: string;
  level?: string;
  message_de?: string;
  pay_url?: string | null;
};

type OpsVendor = {
  id: string;
  name: string;
  category?: string;
  pay_url?: string | null;
  account_url?: string | null;
  note?: string;
  integration?: string;
  pay_ready?: boolean;
};

type HealthItem = {
  id: string;
  name: string;
  status: string;
  detail?: string;
  integration?: string;
};

type FinanceOps = {
  disclaimer_de?: string;
  reality_note_de?: string;
  empty?: boolean;
  income?: { total_eur: number; rows: OpsRow[] };
  expenses?: { total_eur: number; rows: OpsRow[] };
  invoices?: { count: number; rows: OpsRow[] };
  billing_monitor?: { alerts: OpsAlert[] };
  payment_center?: { vendors: OpsVendor[] };
  infrastructure_health?: { overall: string; items: HealthItem[]; legend_de?: string };
  missing_documents?: OpsAlert[];
  morning_brief?: {
    headline_de: string;
    lines: { icon: string; text: string }[];
    attention: OpsAlert[];
    note_de?: string;
  };
  tax_export?: { label_de: string; endpoint: string; includes: string[] };
};

function statusDot(status: string) {
  if (status === "red") return "bg-rose-400";
  if (status === "amber") return "bg-amber-400";
  return "bg-emerald-400";
}

export function FinanceOpsCenter() {
  const [ops, setOps] = useState<FinanceOps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/finance/ops`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setOps(await res.json());
      setError(null);
    } catch {
      setError("Finance & Tax Center nicht erreichbar");
      setOps(null);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const downloadTaxExport = useCallback(async () => {
    setExporting(true);
    setExportMsg(null);
    try {
      const res = await fetch(`${API}/api/owner/finance/tax-export`);
      if (!res.ok) throw new Error("export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `virtus_steuer_export_${new Date().getFullYear()}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      setExportMsg("ZIP heruntergeladen (auch ohne Belege — leere Ordner + Uebersicht.csv).");
    } catch {
      setExportMsg("Export fehlgeschlagen — Backend prüfen.");
    } finally {
      setExporting(false);
    }
  }, []);

  if (error) {
    return (
      <GenesisCard title="Finance & Tax Center" subtitle="CEO">
        <p className="text-sm text-amber-200">{error}</p>
      </GenesisCard>
    );
  }

  if (!ops) {
    return (
      <GenesisCard title="Finance & Tax Center" subtitle="CEO">
        <p className="text-sm text-genesis-muted">Laden…</p>
      </GenesisCard>
    );
  }

  const health = ops.infrastructure_health;
  const brief = ops.morning_brief;
  const isEmpty = Boolean(ops.empty);

  return (
    <div className="space-y-5">
      <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 to-transparent p-5">
        <p className="genesis-label">Finance & Tax Center</p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight">
          {brief?.headline_de ?? "Betrieb · Finanzen · Belege"}
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-genesis-muted">{ops.disclaimer_de}</p>
        {ops.reality_note_de ? (
          <p className="mt-2 rounded-xl border border-amber-500/25 bg-amber-950/20 px-3 py-2 text-xs leading-relaxed text-amber-100/90">
            {ops.reality_note_de}
          </p>
        ) : null}
        {brief ? (
          <ul className="mt-4 grid gap-2 sm:grid-cols-2">
            {brief.lines.map((line) => (
              <li
                key={line.text}
                className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-genesis-text"
              >
                {line.text}
              </li>
            ))}
          </ul>
        ) : null}
      </header>

      {isEmpty ? (
        <div className="rounded-2xl border border-sky-500/25 bg-sky-950/20 px-4 py-4 text-sm text-sky-100/90">
          Noch keine Dokumente. Sie erscheinen automatisch nach den ersten bezahlten Aufträgen
          und wenn Sie Ausgaben/Belege hinzufügen. Export für Steuerberater funktioniert auch
          jetzt (leere Ordner + Übersicht).
        </div>
      ) : null}

      {health ? (
        <GenesisCard
          title="Infrastructure Health"
          subtitle={`Gesamt: ${health.overall === "green" ? "stabil" : health.overall === "amber" ? "prüfen" : "Handlung nötig"}`}
        >
          {health.legend_de ? (
            <p className="mb-3 text-xs text-genesis-muted">{health.legend_de}</p>
          ) : null}
          <ul className="space-y-2">
            {health.items.map((item) => (
              <li
                key={item.id}
                className="flex items-start gap-3 rounded-xl border border-genesis-border-subtle px-3 py-2 text-sm"
              >
                <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${statusDot(item.status)}`} />
                <div>
                  <p className="font-medium">
                    {item.name}{" "}
                    <span className="text-xs font-normal text-genesis-muted">
                      · {item.integration === "not_configured" ? "Link fehlt" : "manueller Link"}
                    </span>
                  </p>
                  <p className="text-xs text-genesis-muted">{item.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </GenesisCard>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <GenesisCard title="1 · Finanzen" subtitle="Einnahmen & Ausgaben">
          <div className="mb-3 grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-950/20 px-3 py-2">
              <p className="text-xs text-genesis-muted">Einnahmen</p>
              <p className="text-lg font-bold tabular-nums">{formatEur(ops.income?.total_eur ?? 0)}</p>
            </div>
            <div className="rounded-xl border border-rose-500/20 bg-rose-950/20 px-3 py-2">
              <p className="text-xs text-genesis-muted">Ausgaben (Belege)</p>
              <p className="text-lg font-bold tabular-nums">{formatEur(ops.expenses?.total_eur ?? 0)}</p>
            </div>
          </div>
          <p className="mb-2 text-xs font-medium text-genesis-muted">
            Belege / Rechnungen: {ops.invoices?.count ?? 0}
          </p>
          {isEmpty ? (
            <p className="text-xs text-genesis-muted">
              Noch leer — nach erster Stripe-Zahlung erscheinen Einnahmen hier.
            </p>
          ) : (
            <ul className="max-h-48 space-y-1 overflow-y-auto text-xs text-genesis-muted">
              {(ops.income?.rows ?? []).slice(0, 6).map((row) => (
                <li key={String(row.order_id || row.label)}>
                  + {formatEur(row.amount_eur ?? 0)} · {row.label} · {row.date}
                </li>
              ))}
              {(ops.expenses?.rows ?? []).slice(0, 6).map((row) => (
                <li key={String(row.id || row.vendor)}>
                  − {formatEur(row.amount_eur ?? 0)} · {row.vendor} · {row.category}
                </li>
              ))}
            </ul>
          )}
        </GenesisCard>

        <GenesisCard title="2 · Billing Monitor" subtitle="Nur echte Hinweise">
          <ul className="space-y-2 text-sm">
            {(ops.billing_monitor?.alerts ?? []).length === 0 ? (
              <li className="text-genesis-muted">
                Keine aktiven Hinweise. Verlängerungsdaten tragen Sie in{" "}
                <code className="text-xs">finance_ops_alerts.json</code> ein — keine Fake-Countdown.
              </li>
            ) : (
              (ops.billing_monitor?.alerts ?? []).map((a) => (
                <li key={a.id || a.message_de} className="rounded-lg border border-white/10 px-3 py-2">
                  <p>{a.message_de}</p>
                  {a.pay_url ? (
                    <a
                      href={a.pay_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-block text-xs text-genesis-accent hover:underline"
                    >
                      Öffnen →
                    </a>
                  ) : null}
                </li>
              ))
            )}
          </ul>
        </GenesisCard>
      </div>

      <GenesisCard title="3 · Zahlungszentrum" subtitle="Offizielle Billing-Seiten (manuell)">
        <div className="grid gap-2 sm:grid-cols-2">
          {(ops.payment_center?.vendors ?? []).map((v) => {
            const href = (v.pay_url || v.account_url || "").trim();
            const ready = Boolean(v.pay_ready && href);
            return (
              <div
                key={v.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-genesis-border-subtle px-3 py-2.5"
              >
                <div>
                  <p className="text-sm font-medium">{v.name}</p>
                  <p className="text-xs text-genesis-muted">{v.note}</p>
                  {!ready ? (
                    <p className="mt-1 text-xs text-amber-200/90">Link nicht konfiguriert</p>
                  ) : (
                    <p className="mt-1 text-xs text-genesis-muted">Manueller Link · kein Auto-Import</p>
                  )}
                </div>
                {ready ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0 rounded-lg bg-genesis-accent/90 px-3 py-1.5 text-xs font-semibold text-white hover:brightness-110"
                  >
                    Bezahlen →
                  </a>
                ) : (
                  <span className="shrink-0 rounded-lg border border-white/15 px-3 py-1.5 text-xs text-genesis-muted">
                    Nicht bereit
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </GenesisCard>

      {(ops.missing_documents ?? []).length > 0 ? (
        <GenesisCard title="Fehlende Belege" subtitle="Zahlung ohne Rechnung">
          <ul className="space-y-2 text-sm text-amber-100/90">
            {(ops.missing_documents ?? []).slice(0, 8).map((m, i) => (
              <li key={`${m.message_de}-${i}`}>{m.message_de}</li>
            ))}
          </ul>
        </GenesisCard>
      ) : null}

      <GenesisCard title="Steuer-Archiv" subtitle="Export für Steuerberater">
        <p className="text-sm text-genesis-muted">
          ZIP mit Ordnern Einnahmen / Ausgaben / Stripe / Domains / Hosting / APIs + Uebersicht.csv.
          Funktioniert auch ohne Belege. Keine automatische Steuerberechnung.
        </p>
        <button
          type="button"
          onClick={downloadTaxExport}
          disabled={exporting}
          className="mt-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow disabled:opacity-50"
        >
          {exporting ? "Export…" : ops.tax_export?.label_de ?? "Export für Steuerberater"}
        </button>
        {exportMsg ? <p className="mt-2 text-xs text-genesis-muted">{exportMsg}</p> : null}
      </GenesisCard>
    </div>
  );
}
