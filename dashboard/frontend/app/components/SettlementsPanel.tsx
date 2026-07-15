"use client";

import { formatEur } from "../lib/formatEur";

export type SettlementRow = {
  settlement_id?: string;
  payment_id?: string;
  amount_eur: number;
  provider?: string;
  label?: string;
  paid_at?: string;
  available_at?: string;
  settlement_status?: string;
  settlement_status_ru?: string;
};

function formatDt(iso: string | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("ru-DE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso.slice(0, 16).replace("T", " ");
  }
}

function statusBadge(status: string | undefined): { label: string; className: string } {
  switch (status) {
    case "available_for_withdrawal":
      return {
        label: "Available",
        className: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
      };
    case "withdrawn":
      return {
        label: "Withdrawn",
        className: "bg-sky-500/15 text-sky-200 border-sky-500/30",
      };
    case "pending_settlement":
    default:
      return {
        label: "Settling",
        className: "bg-amber-500/15 text-amber-200 border-amber-500/30",
      };
  }
}

type Props = {
  rows: SettlementRow[];
  note?: string;
  pendingTotalEur?: number;
  availableTotalEur?: number;
};

export function SettlementsPanel({ rows, note, pendingTotalEur, availableTotalEur }: Props) {
  return (
    <section className="rounded-2xl border border-emerald-500/30 bg-emerald-950/10 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Settlements · Stripe DE</h2>
          <p className="mt-1 text-xs text-genesis-muted">
            {note ??
              "Каждый webhook-платёж — отдельная строка. Settling ≈ 3 рабочих дня до Available."}
          </p>
        </div>
        <div className="flex gap-4 text-xs tabular-nums">
          <span className="text-amber-200/90">
            Settling: {formatEur(pendingTotalEur ?? 0)}
          </span>
          <span className="text-emerald-300">
            Available: {formatEur(availableTotalEur ?? 0)}
          </span>
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed border-genesis-border px-4 py-6 text-center text-sm text-genesis-muted">
          Пока нет записей в finance_settlements.jsonl. После тестовой оплаты через Stripe webhook здесь
          появится строка с датой, суммой и статусом Settling.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-xl border border-genesis-border-subtle">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-genesis-border-subtle bg-genesis-bg/40 text-xs uppercase tracking-wide text-genesis-muted">
                <th className="px-4 py-3 font-medium">Дата транзакции</th>
                <th className="px-4 py-3 font-medium">Сумма</th>
                <th className="px-4 py-3 font-medium">Статус</th>
                <th className="px-4 py-3 font-medium">Available at</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Описание</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-genesis-border-subtle">
              {rows.map((row) => {
                const badge = statusBadge(row.settlement_status);
                return (
                  <tr key={row.settlement_id ?? row.payment_id} className="hover:bg-white/[0.02]">
                    <td className="whitespace-nowrap px-4 py-3 tabular-nums text-genesis-muted">
                      {formatDt(row.paid_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-semibold tabular-nums">
                      {formatEur(row.amount_eur)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge.className}`}
                        title={row.settlement_status_ru}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 tabular-nums text-genesis-muted">
                      {formatDt(row.available_at)}
                    </td>
                    <td className="hidden max-w-[200px] truncate px-4 py-3 text-xs text-genesis-muted sm:table-cell">
                      {row.label ?? row.provider ?? "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
