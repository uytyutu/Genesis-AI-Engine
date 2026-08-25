"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
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
  layer?: string;
  receipt_url?: string | null;
  payment_id?: string | null;
  quelle?: string;
  note_de?: string;
};

type OpsAlert = {
  id?: string;
  level?: string;
  message_de?: string;
  pay_url?: string | null;
  receipt_url?: string | null;
  order_id?: string;
};

type HealthItem = {
  id: string;
  name: string;
  status: string;
  detail?: string;
  integration?: string;
  stack_role?: string;
  href?: string | null;
  pay_url?: string | null;
  account_url?: string | null;
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
  stack_role?: string;
  health?: string;
};

type LayerBlock = {
  total_eur?: number;
  quelle_de?: string;
  rows?: OpsRow[];
};

type FinanceOps = {
  version?: string;
  disclaimer_de?: string;
  reality_note_de?: string;
  stack_map_de?: string;
  empty?: boolean;
  layers?: {
    REAL?: LayerBlock;
    DEMO_TEST?: LayerBlock;
    AUSZAHLBAR?: LayerBlock;
  };
  income?: { total_eur: number; rows: OpsRow[]; quelle_de?: string; sources?: string[] };
  demo_test_income?: { total_eur: number; rows: OpsRow[]; quelle_de?: string };
  auszahlbar?: { total_eur: number; quelle_de?: string };
  expenses?: {
    total_eur: number;
    rows: OpsRow[];
    quelle_de?: string;
    pending_without_pdf?: number;
  };
  invoices?: { count: number; rows: OpsRow[]; quelle_de?: string };
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
  tax_export?: { label_de: string; endpoint: string; includes: string[]; note_de?: string };
  finanzamt_report?: {
    authority?: string;
    authority_note_de?: string;
    year?: number;
    currency?: string;
    vat_rate_percent?: number | null;
    einnahmen_eur?: number;
    ausgaben_eur?: number;
    ueberschuss_eur?: number;
    ust_ruecklage_eur?: number | null;
    nach_ruecklage_eur?: number | null;
    income_count?: number;
    expense_count?: number;
    disclaimer_de?: string;
    download_zip?: string;
    download_html?: string;
    quelle_de?: string;
    steuerprofil?: {
      configured?: boolean;
      status_de?: string;
      vat_rate_percent?: number | null;
      kleinunternehmer?: boolean | null;
      steuerberater_modus?: string | null;
    };
  };
};

function statusDot(status: string) {
  if (status === "red") return "bg-rose-400";
  if (status === "amber") return "bg-amber-400";
  return "bg-emerald-400";
}

function Quelle({ text }: { text?: string }) {
  if (!text) return null;
  return <p className="mt-1 text-[10px] leading-snug text-zinc-500">Quelle: {text}</p>;
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
      const year = ops?.finanzamt_report?.year ?? new Date().getFullYear();
      const res = await fetch(`${API}/api/owner/finance/tax-export?year=${year}`);
      if (!res.ok) throw new Error("export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `virtus_finanzamt_bericht_${year}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      setExportMsg(
        `Finanzamt-Bericht ${year} heruntergeladen (nur REAL Ledger · ohne Demo/Test).`,
      );
    } catch {
      setExportMsg("Export fehlgeschlagen — Backend prüfen.");
    } finally {
      setExporting(false);
    }
  }, [ops?.finanzamt_report?.year]);

  const openFinanzamtHtml = useCallback(() => {
    const year = ops?.finanzamt_report?.year ?? new Date().getFullYear();
    window.open(`${API}/api/owner/finance/finanzamt-report.html?year=${year}`, "_blank");
  }, [ops?.finanzamt_report?.year]);

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
  const realEur = ops.layers?.REAL?.total_eur ?? ops.income?.total_eur ?? 0;
  const demoEur = ops.layers?.DEMO_TEST?.total_eur ?? ops.demo_test_income?.total_eur ?? 0;
  const auszahlbarEur = ops.layers?.AUSZAHLBAR?.total_eur ?? ops.auszahlbar?.total_eur ?? 0;
  const profil = ops.finanzamt_report?.steuerprofil;
  const demoRows = ops.demo_test_income?.rows ?? ops.layers?.DEMO_TEST?.rows ?? [];

  return (
    <div className="space-y-5">
      <header className="rounded-2xl border border-emerald-500/25 bg-gradient-to-br from-emerald-950/30 to-transparent p-5">
        <p className="genesis-label">Finance & Tax Center 2.0 · Financial Truth</p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight">
          {brief?.headline_de ?? "Betrieb · Finanzen · Belege"}
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-genesis-muted">{ops.disclaimer_de}</p>
        {ops.reality_note_de ? (
          <p className="mt-2 rounded-xl border border-amber-500/25 bg-amber-950/20 px-3 py-2 text-xs leading-relaxed text-amber-100/90">
            {ops.reality_note_de}
          </p>
        ) : null}
        {ops.stack_map_de ? (
          <p className="mt-2 text-[11px] text-zinc-400">{ops.stack_map_de}</p>
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

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-4">
          <p className="text-xs uppercase tracking-wide text-emerald-200/80">REAL Einnahmen</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-white">{formatEur(realEur)}</p>
          <Quelle text={ops.layers?.REAL?.quelle_de ?? ops.income?.quelle_de} />
        </div>
        <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-4">
          <p className="text-xs uppercase tracking-wide text-amber-200/80">DEMO / TEST</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-amber-100">
            {formatEur(demoEur)}
          </p>
          <Quelle text={ops.layers?.DEMO_TEST?.quelle_de ?? ops.demo_test_income?.quelle_de} />
          <p className="mt-1 text-[10px] text-amber-200/70">Nicht für Finanzamt / DATEV</p>
        </div>
        <div className="rounded-2xl border border-sky-500/30 bg-sky-950/20 p-4">
          <p className="text-xs uppercase tracking-wide text-sky-200/80">Auszahlbar</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-sky-100">
            {formatEur(auszahlbarEur)}
          </p>
          <Quelle text={ops.layers?.AUSZAHLBAR?.quelle_de ?? ops.auszahlbar?.quelle_de} />
        </div>
      </div>

      {isEmpty ? (
        <div className="rounded-2xl border border-sky-500/25 bg-sky-950/20 px-4 py-4 text-sm text-sky-100/90">
          REAL Einnahmen: <strong>0,00 €</strong> — noch keine bestätigte Live-Zahlung im Ledger.
          Das ist korrekt bis zum ersten Stripe-Webhook → Payment ID → CONFIRMED. Demo/Test unten
          zählen nicht als Umsatz.
        </div>
      ) : null}

      <GenesisCard title="1 · Finanzen" subtitle="REAL vs DEMO getrennt">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-genesis-muted">REAL Einnahmen</p>
            <p className="text-lg font-semibold tabular-nums text-emerald-300">
              {formatEur(realEur)}
            </p>
            <Quelle text={ops.income?.quelle_de} />
          </div>
          <div>
            <p className="text-xs text-genesis-muted">Ausgaben (Belege mit PDF)</p>
            <p className="text-lg font-semibold tabular-nums text-white">
              {formatEur(ops.expenses?.total_eur ?? 0)}
            </p>
            <Quelle text={ops.expenses?.quelle_de} />
          </div>
        </div>
        <p className="mt-3 text-xs text-genesis-muted">
          Belege / Rechnungen (PDF): {ops.invoices?.count ?? 0}
          {(ops.expenses?.pending_without_pdf ?? 0) > 0
            ? ` · ${ops.expenses?.pending_without_pdf} Einträge ohne PDF (nicht steuerrelevant)`
            : null}
        </p>
        <Quelle text={ops.invoices?.quelle_de} />
        {realEur === 0 ? (
          <p className="mt-3 text-xs text-sky-200/90">
            Noch leer für REAL — nach erster Live-Stripe-Zahlung erscheinen Einnahmen hier.
          </p>
        ) : null}
      </GenesisCard>

      {demoRows.length > 0 ? (
        <GenesisCard
          title="DEMO / TEST Aufträge"
          subtitle="Nur Sichtbarkeit · nie Steuerexport"
        >
          <ul className="max-h-56 space-y-2 overflow-y-auto text-sm">
            {demoRows.slice(0, 12).map((r) => (
              <li
                key={`${r.order_id}-${r.date}`}
                className="flex flex-wrap items-baseline justify-between gap-2 border-b border-white/5 pb-2"
              >
                <span className="text-genesis-text">
                  <span className="mr-2 rounded border border-amber-500/30 px-1.5 py-0.5 text-[10px] uppercase text-amber-200">
                    {r.layer || "demo"}
                  </span>
                  {r.label} · {r.order_id}
                </span>
                <span className="tabular-nums text-amber-100">
                  {formatEur(Number(r.amount_eur ?? 0))}
                </span>
                {r.receipt_url ? (
                  <Link
                    href={r.receipt_url}
                    className="w-full text-[11px] text-sky-300 hover:underline"
                  >
                    Order → Receipt {r.receipt_url}
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
          <Quelle text={ops.demo_test_income?.quelle_de} />
        </GenesisCard>
      ) : null}

      <GenesisCard title="2 · Infrastruktur / Billing-Links" subtitle="manuell · kein Auto-Import">
        <p className="mb-3 text-xs text-genesis-muted">{health?.legend_de}</p>
        <div className="space-y-2">
          {(health?.items ?? []).map((item) => {
            const href = item.href || item.pay_url || item.account_url;
            return (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <span className={`h-2 w-2 shrink-0 rounded-full ${statusDot(item.status)}`} />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-white">{item.name}</p>
                    <p className="truncate text-[11px] text-genesis-muted">
                      {item.integration === "manual_link"
                        ? "manueller Link · kein Auto-Import"
                        : item.integration}{" "}
                      · {item.detail}
                    </p>
                  </div>
                </div>
                {href ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 rounded-lg border border-emerald-500/30 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/40"
                  >
                    Öffnen
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
        <GenesisCard title="Belege & Hinweise" subtitle="Order → Receipt/Invoice">
          <ul className="space-y-2 text-sm text-amber-100/90">
            {(ops.missing_documents ?? []).slice(0, 10).map((m, i) => (
              <li key={`${m.message_de}-${i}`}>
                {m.message_de}
                {m.receipt_url ? (
                  <>
                    {" "}
                    <Link href={m.receipt_url} className="text-sky-300 hover:underline">
                      Receipt öffnen
                    </Link>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
          {(ops.invoices?.count ?? 0) === 0 ? (
            <p className="mt-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-genesis-muted">
              Keine Belege vorhanden — keine fiktiven .txt als Ersatz. Nach Live-Zahlung: Payment
              → Ledger → Rechnung/PDF.
            </p>
          ) : null}
        </GenesisCard>
      ) : null}

      <GenesisCard
        title="Finanzamt-Bericht (Deutschland)"
        subtitle="Nur REAL Ledger · Arbeitshilfe, keine Steuerberatung"
      >
        <p className="text-sm text-genesis-muted">
          {ops.finanzamt_report?.authority_note_de ??
            "Für deutsche Steuerpflichtige: Finanzamt — nicht die US Federal Reserve."}
        </p>
        <Quelle text={ops.finanzamt_report?.quelle_de} />
        <div className="mt-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs text-genesis-muted">
          <p>
            Steuerstatus:{" "}
            <strong className="text-white">{profil?.status_de ?? "Nicht konfiguriert"}</strong>
          </p>
          <p>
            Steuersatz:{" "}
            {profil?.configured && profil.vat_rate_percent != null
              ? `${profil.vat_rate_percent} %`
              : "—"}
          </p>
          <p>
            Kleinunternehmerregelung:{" "}
            {profil?.kleinunternehmer == null ? "—" : profil.kleinunternehmer ? "Ja" : "Nein"}
          </p>
          <p>Steuerberater-Modus: {profil?.steuerberater_modus ?? "—"}</p>
        </div>
        {ops.finanzamt_report ? (
          <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
            <table className="w-full text-sm">
              <tbody>
                {(
                  [
                    ["Jahr", String(ops.finanzamt_report.year ?? "—")],
                    [
                      "Einnahmen (REAL)",
                      formatEur(Number(ops.finanzamt_report.einnahmen_eur ?? 0)),
                    ],
                    [
                      "Ausgaben (PDF-Belege)",
                      formatEur(Number(ops.finanzamt_report.ausgaben_eur ?? 0)),
                    ],
                    [
                      "Überschuss (EÜR-lite)",
                      formatEur(Number(ops.finanzamt_report.ueberschuss_eur ?? 0)),
                    ],
                    [
                      profil?.configured && ops.finanzamt_report.vat_rate_percent != null
                        ? `USt-/Steuer-Rücklage (${ops.finanzamt_report.vat_rate_percent}%)`
                        : "USt-/Steuer-Rücklage",
                      ops.finanzamt_report.ust_ruecklage_eur == null
                        ? "Nicht berechnet"
                        : formatEur(Number(ops.finanzamt_report.ust_ruecklage_eur)),
                    ],
                    [
                      "Nach Rücklage (Orientierung)",
                      ops.finanzamt_report.nach_ruecklage_eur == null
                        ? "—"
                        : formatEur(Number(ops.finanzamt_report.nach_ruecklage_eur)),
                    ],
                  ] as const
                ).map(([label, value]) => (
                  <tr key={label} className="border-b border-white/5 last:border-0">
                    <td className="px-3 py-2 text-genesis-muted">{label}</td>
                    <td className="px-3 py-2 text-right font-medium tabular-nums text-white">
                      {value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <p className="mt-3 text-xs text-genesis-muted">
          {ops.finanzamt_report?.disclaimer_de ??
            "Keine ELSTER-Anmeldung — nur REAL Ledger. Mit Steuerberater prüfen."}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={downloadTaxExport}
            disabled={exporting}
            className="rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow disabled:opacity-50"
          >
            {exporting
              ? "Export…"
              : ops.tax_export?.label_de ?? "Finanzamt-Bericht herunterladen (ZIP)"}
          </button>
          <button
            type="button"
            onClick={openFinanzamtHtml}
            className="rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10"
          >
            Bericht öffnen (HTML → Drucken/PDF)
          </button>
        </div>
        {ops.tax_export?.note_de ? (
          <p className="mt-2 text-[11px] text-zinc-500">{ops.tax_export.note_de}</p>
        ) : null}
        {exportMsg ? <p className="mt-2 text-xs text-genesis-muted">{exportMsg}</p> : null}
      </GenesisCard>

      <GenesisCard title="Steuer-Archiv" subtitle="ZIP = nur REAL">
        <p className="text-sm text-genesis-muted">
          Derselbe ZIP enthält Ledger_REAL.csv, Finanzamt_Bericht.html/.csv und Belege nur mit
          echtem PDF. Bei REAL = 0 €: ehrlicher Nullbericht — keine Demo-11.630 €.
        </p>
      </GenesisCard>
    </div>
  );
}
