"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { sortOwnedUtxosByLiquidity } from "../../lib/treasury/assetPriority";
import { DEFAULT_SAT_PER_VBYTE, estimateConsolidationFee, PortfolioOptimizer } from "../../lib/treasury/portfolioOptimizer";
import { TreasuryEngine } from "../../lib/treasury/treasuryEngine";
import type { ConsolidationPlan, TreasuryStorageSnapshot } from "../../lib/treasury/types";
import { AutonomousAgentPanel } from "./AutonomousAgentPanel";
import { OkProtocolModal } from "./OkProtocolModal";
import { ValueHunterPanel } from "./ValueHunterPanel";
import { CounterLiquidityLab } from "./CounterLiquidityLab";
import { Bip39ComputeLabPanel } from "./Bip39ComputeLabPanel";
import { OpportunityAIPanel } from "./OpportunityAIPanel";
import { ProtocolStateDiscoveryPanel } from "./ProtocolStateDiscoveryPanel";
import { VcoreConversionPanel } from "./VcoreConversionPanel";
import { VcoreGenesisPanel } from "./VcoreGenesisPanel";
import { VcoreExchangeabilityPanel } from "./VcoreExchangeabilityPanel";
import { VcoreResearchLab } from "./VcoreResearchLab";
import { VcoreRouteFinderPanel } from "./VcoreRouteFinderPanel";

/** Тяжёлая Web3-панель — только по запросу, чтобы /treasury сразу открывался. */
const Web3TreasuryPanel = dynamic(
  () => import("./Web3TreasuryPanel").then((m) => m.Web3TreasuryPanel),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-6 text-center text-xs text-zinc-500">
        Загрузка панели ETH/BTC…
      </div>
    ),
  },
);

function Tip({ text }: { text: string }) {
  return (
    <span
      className="ml-1 inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full border border-zinc-600 text-[10px] text-zinc-400"
      title={text}
      aria-label={text}
    >
      ?
    </span>
  );
}

export function TreasuryDashboard() {
  const engine = useMemo(() => TreasuryEngine.getInstance(), []);
  const optimizer = useMemo(() => new PortfolioOptimizer(), []);
  const [snap, setSnap] = useState<TreasuryStorageSnapshot | null>(null);
  const [vaultDraft, setVaultDraft] = useState("");
  const [label, setLabel] = useState("Мой кошелёк");
  const [address, setAddress] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [okPlan, setOkPlan] = useState<ConsolidationPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [showWeb3, setShowWeb3] = useState(true);

  const refresh = useCallback(() => {
    const s = engine.getSnapshot();
    setSnap(s);
    setVaultDraft(s.vaultAddress);
  }, [engine]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const audit = useMemo(() => {
    if (!snap) return null;
    return optimizer.assess(snap.addresses, snap.utxos);
  }, [snap, optimizer]);

  const prioritizedUtxos = useMemo(() => {
    if (!snap) return [];
    const fee = estimateConsolidationFee(1, 1, DEFAULT_SAT_PER_VBYTE).estimatedFeeSats;
    return sortOwnedUtxosByLiquidity(snap.utxos, fee);
  }, [snap]);

  const run = (fn: () => void) => {
    setErr(null);
    setBusy(true);
    try {
      fn();
      refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка действия");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6 text-zinc-100">
      <div className="rounded-xl border border-amber-800/50 bg-amber-950/30 p-4 text-sm text-amber-100 space-y-1">
        <p>
          <strong>Стратегия:</strong> VCORE — мозг поиска внешней ценности, не «магический» обмен в 300 BTC.
          Сначала <span className="font-mono text-amber-50">Охотник источников (€0 капитала)</span>, затем EXIT
          (STON/THOR) только если появился реальный актив.
        </p>
        <p className="text-xs text-amber-100/80">
          Цель: максимум подтверждённого BTC при CAPITAL=€0. Инфраструктура: Genesis · Route Finder · Value Proof ·
          Reality Ledger · Движок эволюции. Система ищет и измеряет — не обещает доход.
        </p>
        <Tip text="REAL только после внешнего подтверждения. Чужие кошельки и эксплойты запрещены." />
      </div>

      <ValueHunterPanel />

      <CounterLiquidityLab />

      <OpportunityAIPanel />

      <ProtocolStateDiscoveryPanel />

      <Bip39ComputeLabPanel />

      <VcoreGenesisPanel />

      <VcoreExchangeabilityPanel />

      <VcoreRouteFinderPanel />

      {!showWeb3 ? (
        <div className="rounded-xl border border-cyan-900/40 bg-zinc-950/80 p-5 text-center space-y-3">
          <p className="text-sm text-zinc-300">MetaMask / ETH Live Audit</p>
          <button
            type="button"
            className="rounded-lg bg-cyan-700 px-4 py-2 text-xs font-bold text-zinc-950"
            onClick={() => setShowWeb3(true)}
          >
            Открыть MetaMask панель
          </button>
        </div>
      ) : (
        <Web3TreasuryPanel autoConnect />
      )}

      <VcoreResearchLab />

      <VcoreConversionPanel />

      <AutonomousAgentPanel />

      {err && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 px-4 py-2 text-sm text-rose-200">{err}</div>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-cyan-400">
            Проверенный Vault
            <Tip text="Ваш основной адрес хранения — куда сводим свои UTXO." />
          </h2>
          <input
            value={vaultDraft}
            onChange={(e) => setVaultDraft(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs"
            placeholder="bc1… ваш Vault"
          />
          <button
            type="button"
            disabled={busy}
            className="rounded-lg bg-cyan-700 px-3 py-2 text-xs font-bold text-zinc-950 hover:bg-cyan-600 disabled:opacity-50"
            onClick={() => run(() => engine.setVaultAddress(vaultDraft))}
          >
            Сохранить адрес Vault
          </button>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-cyan-400">
            Зарегистрировать свой адрес
            <Tip text="Нужно подтверждение владения. Чужие адреса отклоняются." />
          </h2>
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs"
            placeholder="Метка"
          />
          <input
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs"
            placeholder="bc1… адрес, которым владеете"
          />
          <button
            type="button"
            disabled={busy || !address.trim()}
            className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-zinc-950 hover:bg-emerald-600 disabled:opacity-50"
            onClick={() =>
              run(() => {
                engine.registerOwnedAddress({
                  label,
                  address,
                  kind: "hot",
                  ownershipConfirmed: true,
                });
                setAddress("");
              })
            }
          >
            Я владею адресом — зарегистрировать
          </button>
          <button
            type="button"
            disabled={busy}
            className="ml-2 rounded-lg border border-zinc-600 px-3 py-2 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
            onClick={() => run(() => engine.seedDemoOwnedPortfolio())}
          >
            Загрузить демо своих UTXO
            <Tip text="Учебные данные для UI — не поиск в mainnet." />
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
        <h2 className="text-sm font-semibold text-cyan-400">
          Аудит портфеля
          <Tip text="Пыль = хвосты, невыгодные поодиночке; пакет снижает среднюю комиссию на ВАШИХ UTXO." />
        </h2>
        {audit ? (
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs font-mono md:grid-cols-4">
            <Metric label="Своих адресов" value={String(audit.ownedAddressCount)} />
            <Metric label="UTXO" value={String(audit.utxoCount)} />
            <Metric label="Пыль (sats)" value={audit.dustSats.toLocaleString("ru-RU")} />
            <Metric label="Оценка комиссии пакета" value={audit.batchFee.estimatedFeeSats.toLocaleString("ru-RU")} />
            <Metric label="Всего sats" value={audit.totalSats.toLocaleString("ru-RU")} />
            <Metric label="Кандидаты в пакет" value={String(audit.batchCandidateCount)} />
            <Metric label="Пакет выгоден?" value={audit.profitable ? "ДА" : "НЕТ"} />
          </div>
        ) : (
          <p className="mt-2 text-xs text-zinc-500">Пока нет данных.</p>
        )}
        <button
          type="button"
          disabled={busy}
          className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-bold text-zinc-950 hover:bg-emerald-500 disabled:opacity-50"
          onClick={() =>
            run(() => {
              const plan = engine.buildConsolidationPlan();
              setOkPlan(plan);
            })
          }
        >
          Построить план консолидации
        </button>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
        <h2 className="text-sm font-semibold text-cyan-400">
          Приоритетные UTXO (ликвидность / комиссия)
          <Tip text="Сортировка: сумма минус комиссия одиночного перевода — сначала крупнейший net." />
        </h2>
        {prioritizedUtxos.length === 0 ? (
          <p className="mt-2 text-xs text-zinc-500">UTXO пока нет.</p>
        ) : (
          <ul className="mt-3 max-h-56 space-y-2 overflow-y-auto text-xs font-mono">
            {prioritizedUtxos.map((u, i) => (
              <li key={u.id} className="flex items-center justify-between gap-2 rounded border border-zinc-800 p-2">
                <div className="min-w-0">
                  <span className="text-zinc-500">#{i + 1}</span>{" "}
                  <span className="text-emerald-400">{u.amountSats.toLocaleString("ru-RU")} sats</span>
                  <span className="text-zinc-600"> · net≈{u.netAfterFeeSats.toLocaleString("ru-RU")}</span>
                  <div className="truncate text-zinc-500">
                    {u.txid}:{u.vout}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
          <h2 className="text-sm font-semibold text-zinc-200">Свои адреса</h2>
          <ul className="mt-2 max-h-48 space-y-2 overflow-y-auto text-xs font-mono">
            {(snap?.addresses ?? []).map((a) => (
              <li key={a.id} className="rounded border border-zinc-800 p-2">
                <div className="text-emerald-400">{a.label}</div>
                <div className="truncate text-zinc-400">{a.address}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/80 p-4">
          <h2 className="text-sm font-semibold text-zinc-200">Планы</h2>
          <ul className="mt-2 max-h-48 space-y-2 overflow-y-auto text-xs font-mono">
            {(snap?.plans ?? []).map((p) => (
              <li key={p.planId} className="rounded border border-zinc-800 p-2">
                <div className="flex justify-between gap-2">
                  <span className="text-cyan-300">{p.planId}</span>
                  <span className={p.status.includes("SETTLED") ? "text-emerald-400" : "text-amber-300"}>
                    {p.status}
                  </span>
                </div>
                <div className="text-zinc-400">
                  net {p.netOutputSats.toLocaleString("ru-RU")} sats · комиссия ~
                  {p.estimatedFeeSats.toLocaleString("ru-RU")}
                </div>
                {p.status === "OK_CONFIRMED" && (
                  <button
                    type="button"
                    className="mt-2 rounded bg-zinc-800 px-2 py-1 text-[11px] text-emerald-300 hover:bg-zinc-700"
                    onClick={() => run(() => engine.signLocalSimulation(p.planId))}
                  >
                    Локальная подпись (симуляция)
                  </button>
                )}
                {p.status === "AWAITING_OK" && (
                  <button
                    type="button"
                    className="mt-2 rounded bg-indigo-700 px-2 py-1 text-[11px] text-white hover:bg-indigo-600"
                    onClick={() => setOkPlan(p)}
                  >
                    Открыть OK Protocol
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
        <h2 className="text-sm font-semibold text-zinc-200">Журнал активности</h2>
        <div className="mt-2 max-h-56 space-y-1 overflow-y-auto font-mono text-[11px]">
          {(snap?.logs ?? []).map((l) => (
            <div key={l.id} className="border-b border-zinc-900 pb-1">
              <span className="text-zinc-500">[{l.at}]</span>{" "}
              <span
                className={
                  l.level === "SUCCESS"
                    ? "text-emerald-400"
                    : l.level === "WARNING"
                      ? "text-amber-300"
                      : l.level === "ERROR"
                        ? "text-rose-400"
                        : "text-zinc-300"
                }
              >
                {l.message}
              </span>
            </div>
          ))}
        </div>
      </section>

      <OkProtocolModal
        open={!!okPlan && okPlan.status === "AWAITING_OK"}
        planId={okPlan?.planId ?? ""}
        netOutputSats={okPlan?.netOutputSats ?? 0}
        destinationAddress={okPlan?.destinationAddress ?? ""}
        onCancel={() => setOkPlan(null)}
        onConfirm={(phrase) => {
          if (!okPlan) return;
          run(() => {
            engine.confirmOk(okPlan.planId, phrase);
            setOkPlan(null);
          });
        }}
      />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/80 p-3">
      <div className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="mt-1 text-sm text-zinc-100">{value}</div>
    </div>
  );
}
