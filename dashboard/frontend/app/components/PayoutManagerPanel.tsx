"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PayoutMethod = {
  id: string;
  label_ru: string;
  official?: boolean;
};

export type PayoutSource = {
  id: string;
  name: string;
  role: string;
  status: string;
  balance_location_ru: string;
  methods: PayoutMethod[];
  min_note_ru?: string;
  fees_note_ru?: string;
  external_dashboard_url?: string;
  virtus_withdraw_api?: boolean;
  note_ru?: string;
  balance_eur: number;
  balance_label_ru: string;
  withdraw_status_ru: string;
  withdrawable: boolean;
  cta: string;
  cta_label_ru: string;
};

export type PayoutManagerData = {
  title_ru: string;
  subtitle_ru: string;
  rule_ru: string;
  kpi?: {
    revenue_label_ru: string;
    execution_cost_label_ru: string;
    infrastructure_cost_label_ru: string;
    real_profit_label_ru: string;
    formula_ru: string;
    pending_settlement_eur?: number;
  };
  sources: PayoutSource[];
  execution_not_payout?: { id: string; name: string; note_ru: string }[];
  history?: {
    at?: string;
    amount_label_ru: string;
    provider: string;
    status_label_ru: string;
  }[];
  summary?: {
    total_withdrawable_label_ru: string;
    any_withdrawable?: boolean;
    verdict_ru?: string;
    sandbox?: boolean;
  };
};

type Props = {
  data: PayoutManagerData | null | undefined;
  compact?: boolean;
  onWithdrawDone?: () => void;
};

export function PayoutManagerPanel({ data, compact, onWithdrawDone }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [walletId, setWalletId] = useState("bank");

  const withdraw = useCallback(
    async (source: PayoutSource) => {
      if (!source.withdrawable || source.cta !== "virtus_api") return;
      const amount = source.balance_eur;
      if (amount <= 0) return;
      setBusy(true);
      setMessage("");
      try {
        const res = await fetch(`${API}/api/engine/withdraw`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ amount_eur: amount, wallet_id: walletId }),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setMessage(String(body.detail || body.message || "Вывод не выполнен"));
          return;
        }
        setMessage(body.message || `Заявка на ${formatEur(amount)} поставлена в очередь.`);
        onWithdrawDone?.();
      } catch {
        setMessage("Сеть / backend недоступен");
      } finally {
        setBusy(false);
      }
    },
    [onWithdrawDone, walletId],
  );

  if (!data || !Array.isArray(data.sources)) return null;

  const sources = data.sources;
  const exec = Array.isArray(data.execution_not_payout) ? data.execution_not_payout : [];
  const history = Array.isArray(data.history) ? data.history : [];

  return (
    <section className="rounded-2xl border border-emerald-500/35 bg-emerald-950/15 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-emerald-100">{data.title_ru}</h2>
          <p className="mt-1 text-sm text-genesis-muted">{data.subtitle_ru}</p>
          <p className="mt-2 text-xs text-amber-100/85">{data.rule_ru}</p>
        </div>
        {!compact ? (
          <Link
            href="/payout"
            className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-sm text-emerald-200 hover:bg-emerald-950/40"
          >
            Вкладка Вывод →
          </Link>
        ) : null}
      </div>

      {data.kpi ? (
        <div className={`mt-4 grid gap-3 ${compact ? "grid-cols-2" : "sm:grid-cols-4"}`}>
          <KpiCell label="Revenue" value={data.kpi.revenue_label_ru} />
          <KpiCell label="Execution" value={data.kpi.execution_cost_label_ru} />
          <KpiCell label="Infrastructure" value={data.kpi.infrastructure_cost_label_ru} />
          <KpiCell label="REAL PROFIT" value={data.kpi.real_profit_label_ru} accent />
        </div>
      ) : null}
      {data.kpi?.formula_ru ? (
        <p className="mt-2 text-[11px] text-genesis-muted">{data.kpi.formula_ru}</p>
      ) : null}

      <p className="mt-4 text-sm font-medium text-white">
        {data.summary?.verdict_ru ?? "—"}
      </p>

      <div className="mt-4 space-y-3">
        {sources.map((s) => (
          <div
            key={s.id}
            className="rounded-xl border border-white/10 bg-genesis-bg/40 p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium text-white">{s.name}</p>
                <p className="mt-0.5 text-[11px] text-genesis-muted">
                  {s.balance_location_ru} · {s.status}
                </p>
              </div>
              <p className="text-xl font-bold tabular-nums text-emerald-100">
                {s.balance_label_ru}
              </p>
            </div>
            <p className="mt-2 text-xs text-sky-100/90">{s.withdraw_status_ru}</p>
            <ul className="mt-2 flex flex-wrap gap-2 text-[11px]">
              {(s.methods || []).map((m) => (
                <li
                  key={m.id}
                  className="rounded-full border border-white/15 px-2 py-0.5 text-white/80"
                >
                  {m.label_ru}
                  {m.official ? " · офиц." : ""}
                </li>
              ))}
            </ul>
            {s.min_note_ru ? (
              <p className="mt-2 text-[11px] text-genesis-muted">{s.min_note_ru}</p>
            ) : null}
            {s.fees_note_ru ? (
              <p className="text-[11px] text-genesis-muted">{s.fees_note_ru}</p>
            ) : null}
            {s.note_ru ? (
              <p className="mt-1 text-[11px] text-amber-100/80">{s.note_ru}</p>
            ) : null}

            <div className="mt-3 flex flex-wrap items-center gap-2">
              {s.cta === "virtus_api" ? (
                <>
                  <select
                    value={walletId}
                    onChange={(e) => setWalletId(e.target.value)}
                    className="rounded-lg border border-white/15 bg-genesis-bg px-2 py-1.5 text-xs text-white"
                    aria-label="Куда вывести"
                  >
                    <option value="bank">Банк / SEPA</option>
                    <option value="stripe">Stripe payout</option>
                    <option value="paypal">PayPal</option>
                  </select>
                  <button
                    type="button"
                    disabled={busy || !s.withdrawable}
                    onClick={() => void withdraw(s)}
                    className="rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
                  >
                    {busy ? "Заявка…" : s.cta_label_ru}
                  </button>
                </>
              ) : s.external_dashboard_url ? (
                <a
                  href={s.external_dashboard_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl border border-sky-500/40 px-4 py-2 text-sm text-sky-100 hover:bg-sky-950/40"
                >
                  {s.cta_label_ru}
                </a>
              ) : (
                <span className="text-xs text-genesis-muted">{s.cta_label_ru}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {!compact && exec.length ? (
        <div className="mt-4 rounded-xl border border-white/10 bg-genesis-bg/30 p-4">
          <p className="text-[10px] uppercase tracking-widest text-genesis-muted">
            Execution — без вывода
          </p>
          <ul className="mt-2 space-y-2 text-xs text-white/80">
            {exec.map((e) => (
              <li key={e.id}>
                <span className="font-medium text-white/90">{e.name}</span>
                {" — "}
                {e.note_ru}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!compact && history.length ? (
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-widest text-genesis-muted">
            История заявок на вывод
          </p>
          <ul className="mt-2 space-y-1 text-xs">
            {history.map((h, i) => (
              <li key={`${h.at}-${i}`} className="flex justify-between gap-2 text-white/85">
                <span>
                  {h.amount_label_ru} · {h.provider}
                </span>
                <span className="text-genesis-muted">
                  {h.status_label_ru}
                  {h.at ? ` · ${String(h.at).slice(0, 16).replace("T", " ")}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {message ? (
        <p className="mt-3 rounded-lg border border-white/10 bg-genesis-bg/50 px-3 py-2 text-xs text-sky-100">
          {message}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <Link href="/finance" className="text-emerald-300 hover:underline">
          Финансы и налоги →
        </Link>
        <Link href="/" className="text-genesis-muted hover:underline">
          Ферма
        </Link>
      </div>
    </section>
  );
}

function KpiCell({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-3 ${
        accent
          ? "border-emerald-500/40 bg-emerald-950/30"
          : "border-white/10 bg-genesis-bg/40"
      }`}
    >
      <p className="text-[10px] uppercase tracking-widest text-genesis-muted">{label}</p>
      <p className="mt-1 text-lg font-bold tabular-nums text-white">{value}</p>
    </div>
  );
}
