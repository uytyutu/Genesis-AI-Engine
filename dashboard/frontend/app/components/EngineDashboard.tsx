"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { formatEur } from "../lib/formatEur";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Target = {
  id: string;
  name: string;
  url: string;
  potential_eur: number;
  profit_score: number;
  traffic_band: string;
  abandoned: boolean;
  status: string;
  status_label: string;
  income_rationale: string;
  revenue_eur: number;
  niche: string;
};

type Wallet = {
  id: string;
  label: string;
  icon: string;
  connected: boolean;
  balance_label?: string | null;
};

type EngineDash = {
  mode: string;
  owner_name: string;
  security_law: string;
  harvest_balance_eur: number;
  lifetime_harvest_eur: number;
  pipeline_potential_eur: number;
  active_assets_count: number;
  available_for_withdrawal_eur: number;
  pending_payouts_eur: number;
  payment_connected: boolean;
  payment_provider_label: string;
  last_sync_at: string | null;
  auto_gate_min_score: number;
  pending_targets: Target[];
  active_assets: Target[];
  wallets: Wallet[];
  withdrawal_enabled: boolean;
};

const TRAFFIC: Record<string, string> = {
  medium: "Средний",
  low: "Низкий",
  trace: "Следы",
};

const WALLET_OPTIONS = [
  { id: "stripe", label: "Stripe" },
  { id: "bank", label: "Банковский счёт" },
  { id: "bitcoin", label: "Bitcoin" },
  { id: "usdt", label: "USDT" },
];

export function EngineDashboard() {
  const [dash, setDash] = useState<EngineDash | null>(null);
  const [scanUrl, setScanUrl] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawWallet, setWithdrawWallet] = useState("stripe");
  const [connectWallet, setConnectWallet] = useState("stripe");
  const [connectLabel, setConnectLabel] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engine/dashboard`);
      if (res.ok) setDash(await res.json());
    } catch {
      setMessage("Не удалось загрузить Engine Mode. Проверьте backend.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = window.setInterval(refresh, 30_000);
    return () => window.clearInterval(t);
  }, [refresh]);

  async function syncPayments() {
    setBusy("sync");
    try {
      const res = await fetch(`${API}/api/engine/sync-payments`, { method: "POST" });
      const body = await res.json();
      setMessage(
        body.stripe_available_eur != null
          ? `Stripe синхронизирован: ${formatEur(body.stripe_available_eur)}`
          : "Синхронизация завершена",
      );
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function runScan(e: React.FormEvent) {
    e.preventDefault();
    if (!scanUrl.trim()) return;
    setBusy("scan");
    setMessage("");
    try {
      const res = await fetch(`${API}/api/engine/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: scanUrl.trim(), niche: "expired_landing" }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Сканирование завершено" : "Ошибка"));
      if (res.ok) setScanUrl("");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function acceptTarget(id: string) {
    setBusy(`accept-${id}`);
    try {
      const res = await fetch(`${API}/api/engine/targets/${id}/accept`, { method: "POST" });
      const body = await res.json();
      setMessage(body.message ?? "Принято");
      refresh();
    } finally {
      setBusy("");
    }
  }

  async function connectPayout(e: React.FormEvent) {
    e.preventDefault();
    if (!connectLabel.trim()) return;
    setBusy("connect");
    try {
      const res = await fetch(`${API}/api/engine/wallets/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_id: connectWallet, account_label: connectLabel.trim() }),
      });
      if (res.ok) {
        setMessage("Счёт привязан для вывода");
        setConnectLabel("");
        refresh();
      }
    } finally {
      setBusy("");
    }
  }

  async function withdraw(e: React.FormEvent) {
    e.preventDefault();
    const amount = parseFloat(withdrawAmount);
    if (!amount || amount <= 0) return;
    setBusy("withdraw");
    try {
      const res = await fetch(`${API}/api/engine/withdraw`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount_eur: amount, wallet_id: withdrawWallet }),
      });
      const body = await res.json();
      setMessage(body.message ?? (res.ok ? "Вывод в очереди" : "Ошибка"));
      if (res.ok) setWithdrawAmount("");
      refresh();
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen pb-16">
      <div className="mx-auto max-w-6xl space-y-6 px-4 pt-6">
        <header className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/40 via-genesis-panel to-genesis-panel p-6">
          <p className="text-xs uppercase tracking-[0.4em] text-amber-300/90">Engine Mode</p>
          <h1 className="mt-2 text-3xl font-bold text-white">
            Движок монетизации · {dash?.owner_name ?? "Владелец"}
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-genesis-muted">
            Автономный сканер рынка → аккумуляция дохода от перехваченных активов. Не продажа услуг — добыча.
          </p>
          {dash?.security_law ? (
            <p className="mt-3 rounded-xl border border-rose-500/30 bg-rose-950/25 px-3 py-2 text-[11px] text-rose-100">
              🔒 {dash.security_law}
            </p>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              disabled={busy === "sync"}
              onClick={() => void syncPayments()}
              className="rounded-lg border border-amber-500/40 bg-amber-950/30 px-3 py-1.5 text-amber-100 hover:bg-amber-900/40 disabled:opacity-50"
            >
              {busy === "sync" ? "Синхронизация…" : "Синхр. Stripe / API"}
            </button>
            <Link href="/monitor" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Классический пульт
            </Link>
            <Link href="/finance" className="rounded-lg border border-genesis-border px-3 py-1.5 hover:bg-genesis-elevated/40">
              Финансы
            </Link>
          </div>
        </header>

        {dash && (
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Kpi label="Баланс добычи" value={formatEur(dash.harvest_balance_eur)} accent />
            <Kpi label="Активные активы" value={String(dash.active_assets_count)} />
            <Kpi label="Потенциал воронки" value={formatEur(dash.pipeline_potential_eur)} />
            <Kpi label="К выводу" value={formatEur(dash.available_for_withdrawal_eur)} accent />
            <Kpi label="Всего добыто" value={formatEur(dash.lifetime_harvest_eur)} />
          </section>
        )}

        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Сканер рынка</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Auto-gate: показываю только цели с score ≥ {dash?.auto_gate_min_score ?? 45}. Остальное отсекается автоматически.
              </p>
              <form onSubmit={runScan} className="mt-4 flex gap-2">
                <input
                  required
                  type="url"
                  value={scanUrl}
                  onChange={(e) => setScanUrl(e.target.value)}
                  placeholder="https://заброшенный-актив.de"
                  className="min-w-0 flex-1 rounded-xl border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "scan"}
                  className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  Сканировать
                </button>
              </form>
            </section>

            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Журнал возможностей — на подтверждение</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Движок уже оценил доходность. Вам остаётся подтвердить перехват.
              </p>
              {!dash?.pending_targets.length ? (
                <p className="mt-4 text-sm text-genesis-muted">Нет целей, прошедших auto-gate. Запустите сканер.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.pending_targets.map((t) => (
                    <TargetCard
                      key={t.id}
                      target={t}
                      busy={busy}
                      onAccept={() => void acceptTarget(t.id)}
                      showAccept
                    />
                  ))}
                </ul>
              )}
            </section>

            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Активные активы</h2>
              <p className="mt-1 text-xs text-genesis-muted">Перехвачены и в монетизации.</p>
              {!dash?.active_assets.length ? (
                <p className="mt-4 text-sm text-genesis-muted">Пока нет — нажмите «Принять в работу» у цели выше.</p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {dash.active_assets.map((t) => (
                    <TargetCard key={t.id} target={t} busy={busy} />
                  ))}
                </ul>
              )}
            </section>
          </div>

          <aside className="space-y-6">
            <section className="genesis-card p-5">
              <h2 className="text-sm font-semibold">Финансовый шлюз</h2>
              <p className="mt-1 text-xs text-genesis-muted">
                Провайдер: {dash?.payment_provider_label ?? "—"} · синхр. {dash?.last_sync_at ? "активна" : "ожидает"}
              </p>
              <p className="mt-3 text-2xl font-bold text-emerald-300">
                {formatEur(dash?.available_for_withdrawal_eur ?? 0)}
              </p>
              <p className="text-[11px] text-genesis-muted">Доступно к выводу</p>
              {dash?.pending_payouts_eur ? (
                <p className="mt-1 text-xs text-amber-200">В очереди: {formatEur(dash.pending_payouts_eur)}</p>
              ) : null}

              <form onSubmit={connectPayout} className="mt-4 space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs font-medium text-white">Привязать счёт</p>
                <select
                  value={connectWallet}
                  onChange={(e) => setConnectWallet(e.target.value)}
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                >
                  {WALLET_OPTIONS.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.label}
                    </option>
                  ))}
                </select>
                <input
                  value={connectLabel}
                  onChange={(e) => setConnectLabel(e.target.value)}
                  placeholder="IBAN / кошелёк / Stripe account"
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "connect"}
                  className="w-full rounded-lg border border-emerald-500/40 py-2 text-xs text-emerald-100"
                >
                  Привязать
                </button>
              </form>

              <form onSubmit={withdraw} className="mt-4 space-y-2 border-t border-white/10 pt-4">
                <p className="text-xs font-medium text-white">Вывод средств</p>
                <select
                  value={withdrawWallet}
                  onChange={(e) => setWithdrawWallet(e.target.value)}
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                >
                  {(dash?.wallets?.length ? dash.wallets.filter((w) => w.connected) : WALLET_OPTIONS).map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.label}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  min={1}
                  step={0.01}
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  placeholder="Сумма €"
                  className="w-full rounded-lg border border-genesis-border bg-genesis-bg px-3 py-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={busy === "withdraw" || !dash?.withdrawal_enabled}
                  className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white disabled:opacity-40"
                >
                  {busy === "withdraw" ? "Обработка…" : "Вывести на счёт"}
                </button>
              </form>

              <p className="mt-3 text-[10px] leading-relaxed text-genesis-muted">
                Синхронизация: <code className="text-amber-200/80">monetization_engine_service.py</code> → Stripe Balance API
                (<code>STRIPE_SECRET_KEY</code>) → очередь <code>finance_payouts.jsonl</code>.
              </p>
            </section>

            {message ? (
              <p className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-genesis-muted">{message}</p>
            ) : null}
          </aside>
        </div>
      </div>
    </main>
  );
}

function TargetCard({
  target: t,
  busy,
  onAccept,
  showAccept,
}: {
  target: Target;
  busy: string;
  onAccept?: () => void;
  showAccept?: boolean;
}) {
  return (
    <li className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-white">{t.name}</p>
          {t.url ? (
            <a href={t.url} target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-300/90 hover:underline">
              {t.url}
            </a>
          ) : null}
        </div>
        <div className="text-right">
          <p className="font-bold text-emerald-300">{formatEur(t.potential_eur)}</p>
          <p className="text-[10px] text-genesis-muted">score {t.profit_score}</p>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-genesis-muted">
        {TRAFFIC[t.traffic_band] ?? t.traffic_band} · {t.abandoned ? "Заброшен" : "Живой"} · {t.status_label}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-genesis-muted">{t.income_rationale}</p>
      {showAccept ? (
        <button
          type="button"
          disabled={busy === `accept-${t.id}`}
          onClick={onAccept}
          className="mt-3 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
        >
          {busy === `accept-${t.id}` ? "Запуск…" : "Принять в работу"}
        </button>
      ) : null}
      {t.revenue_eur > 0 ? (
        <p className="mt-2 text-sm text-emerald-200">Добыча: {formatEur(t.revenue_eur)}</p>
      ) : null}
    </li>
  );
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div
      className={`rounded-xl border p-4 ${
        accent ? "border-amber-500/35 bg-amber-950/20" : "border-genesis-border-subtle bg-genesis-bg/40"
      }`}
    >
      <p className={`text-xl font-bold tabular-nums ${accent ? "text-amber-200" : "text-white"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}
