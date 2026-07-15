"use client";

import { StripeSetupPanel } from "../components/StripeSetupPanel";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { formatEur, formatSignedEur } from "../lib/formatEur";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { GenesisCard } from "../components/GenesisCard";
import { Sparkline } from "../components/Sparkline";
import { WithdrawModal } from "../components/WithdrawModal";
import { PendingPaymentsPanel } from "../components/PendingPaymentsPanel";
import { SettlementsPanel, type SettlementRow } from "../components/SettlementsPanel";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PendingPayment = {
  payment_id: string;
  amount_eur: number;
  label: string;
  provider: string;
  sender: string;
  received_at: string;
};

type Wallet = {
  id: string;
  label: string;
  icon: string;
  connected: boolean;
  balance_label: string | null;
};

type Payout = {
  at: string;
  amount_eur: number;
  provider: string;
  status: string;
  status_label: string;
};

type Finance = {
  greeting: string;
  demo_mode: boolean;
  system_mode?: string;
  payment_connected: boolean;
  payment_provider_label: string;
  data_source_note: string;
  platform_balance_eur: number;
  revenue_today_eur: number;
  revenue_month_eur: number;
  available_for_withdrawal_eur: number;
  pending_payouts_eur: number;
  recent_transactions: { at: string; amount_eur: number; label: string }[];
  withdrawal_enabled: boolean;
  wallets: Wallet[];
  payout_history: Payout[];
  last_withdrawal: { at: string; amount_eur: number; provider: string; status_label: string } | null;
  revenue_sparkline: number[];
  pending_payments: PendingPayment[];
  settlements?: SettlementRow[];
  settlement_note_ru?: string;
  paid_by_client_eur?: number;
  pending_settlement_eur?: number;
  financial_view?: FinancialView;
  global_revenue?: {
    currency: string;
    countries_active: number;
    total_revenue_eur: number;
    total_pipeline_eur: number;
    by_country: { country_code: string; revenue_eur: number; pipeline_eur: number; leads: number }[];
    note: string;
  };
};

type FinancialView = {
  system_mode: string;
  funds_held_by_genesis_eur: number;
  money_never_stored: boolean;
  money_route: string;
  custody_note: string;
  gross_synced_eur: number;
  tax_reserve_eur: number;
  net_clean_eur: number;
  safe_to_withdraw_eur: number;
  safe_to_withdraw_status: "sandbox" | "green" | "amber";
  safe_to_withdraw_label: string;
  pending_at_provider_eur: number;
  paid_by_client_eur?: number;
  pending_settlement_eur?: number;
  potential_revenue_eur: number;
  potential_revenue?: {
    potential_revenue_eur: number;
    pipeline_potential_eur?: number;
    hunter_potential_eur?: number;
    disclaimer?: string;
  };
  reconcile_enabled: boolean;
  withdraw_enabled: boolean;
  last_reconcile_at: string | null;
  disclaimer: string;
};

export default function FinancePage() {
  const [finance, setFinance] = useState<Finance | null>(null);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [reconciling, setReconciling] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/finance`);
      setFinance(await res.json());
    } catch {
      setFinance(null);
    }
  }, []);

  const reconcile = useCallback(async () => {
    setReconciling(true);
    try {
      const res = await fetch(`${API}/api/owner/finance/reconcile`, { method: "POST" });
      if (res.ok) {
        await refresh();
      }
    } finally {
      setReconciling(false);
    }
  }, [refresh]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 10000);
    return () => clearInterval(t);
  }, [refresh]);

  const showLive = finance?.payment_connected || finance?.demo_mode;
  const connectedWallets = finance?.wallets?.filter((w) => w.connected).length ?? 0;
  const view = finance?.financial_view;
  const isSandbox = view?.system_mode === "sandbox" || finance?.system_mode === "sandbox";
  const safeAmount = view?.safe_to_withdraw_eur ?? finance?.available_for_withdrawal_eur ?? 0;
  const canWithdraw = view?.withdraw_enabled ?? finance?.withdrawal_enabled ?? false;

  return (
    <main>
      <div className="mx-auto max-w-3xl space-y-5">
        <header className="animate-fade-up text-center">
          <p className="genesis-label">Financial View</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">{finance?.greeting ?? BRAND_NAME}</h1>
          <p className="mt-2 text-sm text-genesis-muted">{finance?.payment_provider_label ?? "Payment Hub"}</p>
          {isSandbox && (
            <p className="mt-2 inline-block rounded-full border border-sky-500/30 bg-sky-950/30 px-3 py-1 text-xs text-sky-200">
              Sandbox Mode — Potential Revenue, без реальных выплат
            </p>
          )}
          {finance?.demo_mode && (
            <p className="mt-2 inline-block rounded-full border border-amber-500/30 bg-amber-950/30 px-3 py-1 text-xs text-amber-200">
              Демо — не реальные деньги
            </p>
          )}
        </header>

        <StripeSetupPanel />

        {view ? (
          <section className="genesis-card overflow-hidden border-emerald-500/25 p-0">
            <div
              className={`p-6 sm:p-8 ${
                view.safe_to_withdraw_status === "green"
                  ? "bg-gradient-to-br from-emerald-500/15 via-transparent to-genesis-accent/5"
                  : view.safe_to_withdraw_status === "sandbox"
                    ? "bg-gradient-to-br from-sky-500/10 via-transparent to-genesis-accent/5"
                    : "bg-gradient-to-br from-amber-500/10 via-transparent to-genesis-accent/5"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="genesis-label">Safe to Withdraw</p>
                  <p className="mt-1 text-xs text-genesis-muted">{view.safe_to_withdraw_label}</p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    view.safe_to_withdraw_status === "green"
                      ? "bg-emerald-500/20 text-emerald-300"
                      : view.safe_to_withdraw_status === "sandbox"
                        ? "bg-sky-500/20 text-sky-200"
                        : "bg-amber-500/20 text-amber-200"
                  }`}
                >
                  {view.safe_to_withdraw_status === "green"
                    ? "✔ Безопасно к выводу"
                    : view.safe_to_withdraw_status === "sandbox"
                      ? "◎ Sandbox"
                      : "◎ Резерв"}
                </span>
              </div>
              <p className="mt-4 text-4xl font-bold tabular-nums tracking-tight sm:text-5xl">
                {isSandbox ? formatEur(view.potential_revenue_eur) : formatEur(safeAmount)}
              </p>
              <p className="mt-2 text-xs text-genesis-muted">
                {isSandbox
                  ? "Potential Revenue — оценка, не реальный доход"
                  : `Чистая прибыль после резерва: ${formatEur(view.net_clean_eur)}`}
              </p>
            </div>
            <div className="divide-y divide-genesis-border-subtle border-t border-genesis-border-subtle text-sm">
              <FinanceRow
                label="В Genesis (всегда 0 €)"
                value={formatEur(view.funds_held_by_genesis_eur)}
              />
              {!isSandbox && (
                <>
                  <FinanceRow label="Синхронизировано (грязными)" value={formatEur(view.gross_synced_eur)} />
                  <FinanceRow label="Резерв под налоги" value={formatEur(view.tax_reserve_eur)} />
                  <FinanceRow label="Чистая прибыль" value={formatEur(view.net_clean_eur)} highlight />
                  <FinanceRow label="Ожидает у провайдера" value={formatEur(view.pending_at_provider_eur)} />
                </>
              )}
              {isSandbox && view.potential_revenue ? (
                <>
                  <FinanceRow
                    label="Воронка лидов"
                    value={formatEur(view.potential_revenue.pipeline_potential_eur ?? 0)}
                  />
                  <FinanceRow
                    label="Hunter-Gatherer"
                    value={formatEur(view.potential_revenue.hunter_potential_eur ?? 0)}
                  />
                </>
              ) : null}
            </div>
            <div className="border-t border-genesis-border-subtle p-4 space-y-3">
              <p className="text-xs leading-relaxed text-genesis-muted">{view.custody_note}</p>
              <p className="text-xs text-genesis-muted">{view.money_route}</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={!view.reconcile_enabled || reconciling}
                  onClick={reconcile}
                  className="rounded-xl border border-genesis-border px-4 py-2.5 text-xs font-medium hover:bg-genesis-elevated disabled:opacity-40"
                >
                  {reconciling ? "Сверка…" : "Вывести / Сверить с банком"}
                </button>
                {view.last_reconcile_at ? (
                  <span className="self-center text-xs text-genesis-muted">
                    Последняя сверка: {view.last_reconcile_at.slice(0, 19).replace("T", " ")}
                  </span>
                ) : null}
              </div>
            </div>
          </section>
        ) : null}

        <PendingPaymentsPanel payments={finance?.pending_payments ?? []} />

        <SettlementsPanel
          rows={finance?.settlements ?? []}
          note={finance?.settlement_note_ru}
          pendingTotalEur={finance?.pending_settlement_eur ?? view?.pending_settlement_eur}
          availableTotalEur={finance?.available_for_withdrawal_eur}
        />

        {showLive ? (
          <>
            <section className="genesis-card overflow-hidden border-genesis-accent/20 p-0 shadow-glow">
              <div className="bg-gradient-to-br from-genesis-accent/10 via-transparent to-emerald-500/5 p-6 sm:p-8">
                <p className="genesis-label">Выручка к выводу</p>
                <p className="mt-2 text-4xl font-bold tabular-nums tracking-tight sm:text-5xl">
                  {formatEur(finance?.available_for_withdrawal_eur ?? 0)}
                </p>
                <p className="mt-2 text-xs text-genesis-muted">
                  Stripe sync (баланс провайдера): {formatEur(finance?.platform_balance_eur ?? 0)} · только для сверки
                </p>
                <div className="mt-6 h-14">
                  <Sparkline values={finance?.revenue_sparkline ?? []} height={56} />
                </div>
              </div>
              <div className="divide-y divide-genesis-border-subtle border-t border-genesis-border-subtle">
                <FinanceRow label="Оплачено клиентом" value={formatEur(finance?.paid_by_client_eur ?? view?.paid_by_client_eur ?? 0)} />
                <FinanceRow label="Settlement (DE ~3 дня)" value={formatEur(finance?.pending_settlement_eur ?? view?.pending_settlement_eur ?? 0)} />
                <FinanceRow label="Доступно к выводу" value={formatEur(finance?.available_for_withdrawal_eur)} highlight />
                <FinanceRow label="Сегодня" value={`+${formatEur(finance?.revenue_today_eur).replace(" €", "")} €`} positive />
                <FinanceRow label="За месяц" value={`+${formatEur(finance?.revenue_month_eur).replace(" €", "")} €`} positive />
              </div>
            </section>

            {finance?.last_withdrawal && (
              <GenesisCard title="Последний вывод">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <div>
                    <p className="font-semibold tabular-nums">{formatEur(finance.last_withdrawal.amount_eur)}</p>
                    <p className="mt-1 text-genesis-muted">
                      {finance.last_withdrawal.at} · {finance.last_withdrawal.provider}
                    </p>
                  </div>
                  <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-400">
                    ✔ {finance.last_withdrawal.status_label}
                  </span>
                </div>
              </GenesisCard>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                disabled={!canWithdraw}
                onClick={() => setWithdrawOpen(true)}
                className="flex-1 rounded-2xl bg-gradient-to-r from-genesis-accent to-blue-600 py-3.5 text-sm font-semibold text-white shadow-glow disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isSandbox ? "Вывод в Sandbox недоступен" : canWithdraw ? "Вывести средства" : "Вывод после settlement (~3 раб. дня DE)"}
              </button>
              <Link
                href="/"
                className="rounded-2xl border border-genesis-border px-5 py-3.5 text-sm font-medium hover:bg-genesis-elevated"
              >
                ← Virtus Core
              </Link>
            </div>
          </>
        ) : (
          <GenesisCard glow title="Payment Hub" subtitle="Не подключён">
            <p className="text-sm leading-relaxed text-genesis-muted">
              Все средства поступают напрямую на <strong className="text-genesis-text">ваши</strong> счета.
              Virtus Core только отображает операции — не хранит и не переводит деньги.
            </p>
            <p className="mt-4 text-3xl font-bold tabular-nums text-genesis-muted/80">0 €</p>
            <p className="mt-1 text-xs text-genesis-muted">Доход появится после первой реальной оплаты</p>
            <div className="mt-6">
              <Link href="/" className="text-sm text-genesis-accent hover:underline">
                ← Вернуться к цели «До первого клиента»
              </Link>
            </div>
          </GenesisCard>
        )}

        {finance?.global_revenue && finance.global_revenue.by_country.length > 0 ? (
          <GenesisCard
            title="Global Revenue Report"
            subtitle={`${finance.global_revenue.countries_active} стран · ${finance.global_revenue.currency}`}
          >
            <p className="mb-3 text-xs text-genesis-muted">{finance.global_revenue.note}</p>
            <div className="mb-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-genesis-border-subtle px-4 py-3">
                <p className="text-xs text-genesis-muted">Доход по миру</p>
                <p className="text-lg font-bold tabular-nums">{formatEur(finance.global_revenue.total_revenue_eur)}</p>
              </div>
              <div className="rounded-xl border border-genesis-border-subtle px-4 py-3">
                <p className="text-xs text-genesis-muted">Воронка по миру</p>
                <p className="text-lg font-bold tabular-nums">{formatEur(finance.global_revenue.total_pipeline_eur)}</p>
              </div>
            </div>
            <ul className="space-y-2 text-sm">
              {finance.global_revenue.by_country.slice(0, 8).map((row) => (
                <li
                  key={row.country_code}
                  className="flex items-center justify-between gap-3 rounded-lg border border-genesis-border-subtle px-3 py-2"
                >
                  <span className="font-medium">{row.country_code}</span>
                  <span className="text-genesis-muted text-xs">{row.leads} лидов</span>
                  <span className="tabular-nums font-semibold">{formatEur(row.revenue_eur)}</span>
                </li>
              ))}
            </ul>
          </GenesisCard>
        ) : null}

        <GenesisCard
          title="Кошельки"
          subtitle={connectedWallets > 0 ? `${connectedWallets} подключено` : "Подключите один раз — Virtus Core покажет балансы"}
        >
          <ul className="space-y-2">
            {(finance?.wallets ?? DEFAULT_WALLETS).map((w) => (
              <li
                key={w.id}
                className="flex items-center justify-between gap-4 rounded-xl border border-genesis-border-subtle bg-genesis-bg/30 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg">{w.icon}</span>
                  <span className="text-sm font-medium">{w.label}</span>
                </div>
                <div className="text-right">
                  {w.connected ? (
                    <>
                      <p className="text-xs font-medium text-emerald-400">✔ Подключён</p>
                      {w.balance_label && (
                        <p className="mt-0.5 text-sm font-semibold tabular-nums">{w.balance_label}</p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-genesis-muted">Не подключён</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
          {!showLive && (
            <p className="mt-4 text-center text-xs text-genesis-muted">
              Подключение — после первого отзыва реального клиента (Sprint FIRST CUSTOMER)
            </p>
          )}
        </GenesisCard>

        <GenesisCard title="История выплат">
          {(finance?.payout_history?.length ?? 0) === 0 ? (
            <p className="text-sm text-genesis-muted">Пока нет выплат — {BRAND_NAME} покажет их после подключения Payment Hub.</p>
          ) : (
            <ul className="space-y-3">
              {finance!.payout_history.map((p, i) => (
                <li key={`${p.at}-${i}`} className="flex items-center justify-between gap-4 border-b border-genesis-border-subtle pb-3 last:border-0">
                  <div>
                    <p className="text-sm font-semibold tabular-nums">✔ {formatEur(p.amount_eur)}</p>
                    <p className="mt-0.5 text-xs text-genesis-muted">
                      {p.provider} · {p.at}
                    </p>
                  </div>
                  <span className="text-xs text-emerald-400">✔ {p.status_label}</span>
                </li>
              ))}
            </ul>
          )}
        </GenesisCard>

        <GenesisCard title="Последние поступления">
          {(finance?.recent_transactions?.length ?? 0) === 0 ? (
            <p className="text-sm text-genesis-muted">Пока нет поступлений.</p>
          ) : (
            <ul className="space-y-2">
              {finance!.recent_transactions.map((tx, i) => (
                <li key={`${tx.at}-${i}`} className="flex justify-between gap-4 text-sm">
                  <span className="text-genesis-muted">{tx.label}</span>
                  <span className="font-semibold text-emerald-400">{formatSignedEur(tx.amount_eur)}</span>
                </li>
              ))}
            </ul>
          )}
        </GenesisCard>

        <p className="rounded-xl border border-dashed border-genesis-border px-4 py-3 text-xs leading-relaxed text-genesis-muted">
          {finance?.data_source_note}
        </p>

        <GenesisCard title="Отчётность Engine · DATEV">
          <p className="text-sm text-genesis-muted">
            Полный финансовый контур: harvest_ledger + Stripe + crypto → один файл для Steuerberater (Lexoffice/DATEV).
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href="/"
              className="rounded-lg border border-sky-500/40 px-3 py-2 text-xs text-sky-100 hover:bg-sky-950/30"
            >
              Engine → Tax &amp; Accounting
            </Link>
            <a
              href={`${API}/api/engine/accounting/export.datev.csv`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-emerald-500/40 px-3 py-2 text-xs text-emerald-100 hover:bg-emerald-950/30"
            >
              ⬇ Скачать DATEV
            </a>
            <a
              href={`${API}/api/engine/accounting/export.csv`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg border border-white/15 px-3 py-2 text-xs hover:bg-white/5"
            >
              ⬇ CSV Finanzamt
            </a>
          </div>
        </GenesisCard>
      </div>

      <WithdrawModal
        open={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
        amount={safeAmount}
        wallets={finance?.wallets ?? []}
      />
    </main>
  );
}

const DEFAULT_WALLETS: Wallet[] = [
  { id: "bank", label: "Банковский счёт", icon: "🏦", connected: false, balance_label: null },
  { id: "stripe", label: "Stripe", icon: "💳", connected: false, balance_label: null },
  { id: "paypal", label: "PayPal", icon: "🟦", connected: false, balance_label: null },
  { id: "bitcoin", label: "Bitcoin", icon: "₿", connected: false, balance_label: null },
  { id: "usdt", label: "USDT", icon: "💵", connected: false, balance_label: null },
];

function FinanceRow({
  label,
  value,
  highlight,
  positive,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  positive?: boolean;
}) {
  return (
    <div className={`flex justify-between gap-4 px-6 py-4 text-sm ${highlight ? "bg-genesis-bg/30" : ""}`}>
      <span className="text-genesis-muted">{label}</span>
      <span className={`font-semibold tabular-nums ${positive ? "text-emerald-400" : ""}`}>{value}</span>
    </div>
  );
}
