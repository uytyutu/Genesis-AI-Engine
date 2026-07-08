"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur, formatSignedEur } from "../lib/formatEur";
import { BRAND_NAME, ASSISTANT_NAME } from "../lib/publicBrand";
import { GenesisCard } from "../components/GenesisCard";
import { Sparkline } from "../components/Sparkline";
import { WithdrawModal } from "../components/WithdrawModal";
import { PendingPaymentsPanel } from "../components/PendingPaymentsPanel";

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
};

export default function FinancePage() {
  const [finance, setFinance] = useState<Finance | null>(null);
  const [withdrawOpen, setWithdrawOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/finance`);
      setFinance(await res.json());
    } catch {
      setFinance(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 10000);
    return () => clearInterval(t);
  }, [refresh]);

  const showLive = finance?.payment_connected || finance?.demo_mode;
  const connectedWallets = finance?.wallets?.filter((w) => w.connected).length ?? 0;

  return (
    <main>
      <div className="mx-auto max-w-3xl space-y-5">
        <header className="animate-fade-up text-center">
          <p className="genesis-label">Финансовый центр</p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">{finance?.greeting ?? BRAND_NAME}</h1>
          <p className="mt-2 text-sm text-genesis-muted">{finance?.payment_provider_label ?? "Payment Hub"}</p>
          {finance?.demo_mode && (
            <p className="mt-2 inline-block rounded-full border border-amber-500/30 bg-amber-950/30 px-3 py-1 text-xs text-amber-200">
              Демо — не реальные деньги
            </p>
          )}
        </header>

        <PendingPaymentsPanel payments={finance?.pending_payments ?? []} />

        {showLive ? (
          <>
            <section className="genesis-card overflow-hidden border-genesis-accent/20 p-0 shadow-glow">
              <div className="bg-gradient-to-br from-genesis-accent/10 via-transparent to-emerald-500/5 p-6 sm:p-8">
                <p className="genesis-label">Баланс</p>
                <p className="mt-2 text-4xl font-bold tabular-nums tracking-tight sm:text-5xl">
                  {formatEur(finance?.platform_balance_eur)}
                </p>
                <div className="mt-6 h-14">
                  <Sparkline values={finance?.revenue_sparkline ?? []} height={56} />
                </div>
              </div>
              <div className="divide-y divide-genesis-border-subtle border-t border-genesis-border-subtle">
                <FinanceRow label="Доступно" value={formatEur(finance?.available_for_withdrawal_eur)} highlight />
                <FinanceRow label="Ожидает" value={formatEur(finance?.pending_payouts_eur)} />
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
                disabled={!finance?.withdrawal_enabled}
                onClick={() => setWithdrawOpen(true)}
                className="flex-1 rounded-2xl bg-gradient-to-r from-genesis-accent to-blue-600 py-3.5 text-sm font-semibold text-white shadow-glow disabled:cursor-not-allowed disabled:opacity-40"
              >
                Вывести средства
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
      </div>

      <WithdrawModal
        open={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
        amount={finance?.available_for_withdrawal_eur ?? 0}
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
