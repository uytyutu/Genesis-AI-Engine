"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { TREASURY_POLL_MS } from "../../config/treasuryTargets";
import { sortAssetsByLiquidity, type RankedAsset } from "../../lib/treasury/assetPriority";
import { BitcoinTreasuryEngine, type BtcAddressAudit, type BtcFeeAdvice } from "../../lib/treasury/bitcoinEngine";
import type { GasAdvice } from "../../lib/treasury/gasOptimizer";
import { TreasuryMempoolStream, type StreamEvent } from "../../lib/treasury/mempoolStream";
import { exportLiquidityCsv, exportLiquidityJson, exportLogsCsv } from "../../lib/treasury/reportExport";
import {
  SecureWeb3TreasuryEngine,
  waitForProviderQuiet,
  type ChainAsset,
  type SweepBuckets,
  type Web3TreasuryLog,
} from "../../lib/treasury/secureWeb3Engine";
import { sendTreasuryAlert } from "../../lib/treasury/treasuryAlerts";
import { dustClassLabel, DUST_TIP_RU, gasWindowRu, rankReasonRu } from "../../lib/treasury/uiRu";

export function Web3TreasuryPanel({ autoConnect = false }: { autoConnect?: boolean }) {
  const engine = useMemo(() => new SecureWeb3TreasuryEngine(), []);
  const btcEngine = useMemo(() => new BitcoinTreasuryEngine(), []);
  const stream = useMemo(() => new TreasuryMempoolStream(), []);
  const [connected, setConnected] = useState<string | null>(null);
  const [ranked, setRanked] = useState<RankedAsset[]>([]);
  const [buckets, setBuckets] = useState<SweepBuckets>({
    profitable: [],
    dust: [],
    anomalies: [],
    marginal: [],
  });
  const [btcAudits, setBtcAudits] = useState<BtcAddressAudit[]>([]);
  const [vault, setVault] = useState("");
  const [extraList, setExtraList] = useState("");
  const [logs, setLogs] = useState<Web3TreasuryLog[]>([]);
  const [streamLog, setStreamLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingAsset, setPendingAsset] = useState<ChainAsset | null>(null);
  const [batchConfirm, setBatchConfirm] = useState(false);
  const [collectConfirm, setCollectConfirm] = useState(false);
  const [includeMarginal, setIncludeMarginal] = useState(false);
  const [gas, setGas] = useState<GasAdvice | null>(null);
  const [btcFees, setBtcFees] = useState<BtcFeeAdvice | null>(null);
  const [netOk, setNetOk] = useState<boolean | null>(null);
  const [netMeta, setNetMeta] = useState("—");
  const [lastPoll, setLastPoll] = useState<string>("—");
  const [autoPoll, setAutoPoll] = useState(false);
  const [liveFeed, setLiveFeed] = useState(false);
  const [wsOk, setWsOk] = useState<boolean | null>(null);
  const pollBusy = useRef(false);
  const prevBal = useRef<Map<string, string>>(new Map());
  const lastStreamAudit = useRef(0);
  const alertedKeys = useRef<Set<string>>(new Set());

  const refreshLogs = () => setLogs(engine.getLogs());

  const parseExtra = () =>
    extraList
      .split(/[\n,;\s]+/)
      .map((s) => s.trim())
      .filter(Boolean);

  const applyAssets = (found: ChainAsset[], opts?: { alert?: boolean }) => {
    setRanked(sortAssetsByLiquidity(found));
    setBuckets(engine.filterSweepBuckets(found));
    for (const a of found) {
      const key = a.address.toLowerCase();
      const prev = prevBal.current.get(key);
      if (opts?.alert !== false && prev !== undefined && prev !== a.balanceWei) {
        const alertKey = `${key}:${a.balanceWei}`;
        if (!alertedKeys.current.has(alertKey)) {
          alertedKeys.current.add(alertKey);
          void sendTreasuryAlert({
            title: "Изменение баланса ETH",
            body: `${a.address} → ${a.balanceDecimal} ETH`,
            severity: a.balanceDecimal > 1 ? "critical" : "warning",
            address: a.address,
            network: "ETH",
          });
          setStreamLog((s) => [`СИГНАЛ ETH ${a.address.slice(0, 10)}… ${a.balanceDecimal}`, ...s].slice(0, 40));
        }
      }
      prevBal.current.set(key, a.balanceWei);
    }
  };

  const runConfiguredAudit = useCallback(
    async (opts?: { withBtc?: boolean; quiet?: boolean }) => {
      if (pollBusy.current) return;
      pollBusy.current = true;
      if (!opts?.quiet) setBusy(true);
      setErr(null);
      try {
        const ping = await engine.pingNetwork();
        setNetOk(ping.ok);
        setNetMeta(
          ping.ok
            ? `блок ${ping.blockNumber} · ${ping.latencyMs} мс · ${ping.rpc}`
            : `нет связи · ${ping.latencyMs} мс`,
        );

        const advice = await engine.sampleGasAdvice();
        setGas(advice);

        const found = await engine.scanConfiguredTargets(parseExtra());
        applyAssets(found, { alert: !opts?.quiet });

        if (opts?.withBtc !== false) {
          try {
            const fees = await btcEngine.fetchFeeAdvice();
            setBtcFees(fees);
            const btc = await btcEngine.auditConfigured();
            setBtcAudits(btc);
            if (!opts?.quiet) {
              for (const b of btc) {
                if (b.mempoolTxCount > 0 || b.utxos.some((u) => !u.status.confirmed && u.valueSats >= 100_000)) {
                  const k = `btc:${b.address}:${b.mempoolTxCount}`;
                  if (!alertedKeys.current.has(k)) {
                    alertedKeys.current.add(k);
                    void sendTreasuryAlert({
                      title: "BTC: mempool / крупный неподтверждённый UTXO",
                      body: `${b.address} mempoolTx=${b.mempoolTxCount} utxo=${b.utxoCount}`,
                      severity: "warning",
                      address: b.address,
                      network: "BTC",
                    });
                  }
                }
              }
            }
          } catch (e) {
            console.warn(e);
          }
        }

        setLastPoll(new Date().toLocaleTimeString("ru-RU"));
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Ошибка аудита");
        setNetOk(false);
      } finally {
        pollBusy.current = false;
        setBusy(false);
        refreshLogs();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [engine, btcEngine, extraList],
  );

  const connectAndScan = async () => {
    setErr(null);
    setTxHash(null);
    setBusy(true);
    try {
      const { address, assets: found } = await engine.scanConnectedWallet([
        ...engine.loadConfiguredTargets(),
        ...parseExtra(),
      ]);
      setConnected(address);
      applyAssets(found);
      setGas(await engine.sampleGasAdvice());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Не удалось подключить кошелёк");
    } finally {
      setBusy(false);
      refreshLogs();
    }
  };

  useEffect(() => {
    // Не сканируем сеть при открытии страницы — иначе вкладка «висит» на RPC/mempool.
    setStreamLog((s) => ["Готово. MetaMask: нажмите «Подключить кошелёк» или дождитесь авто-запроса.", ...s].slice(0, 40));
  }, []);

  useEffect(() => {
    if (!autoConnect) return;
    let cancelled = false;
    (async () => {
      // MetaMask injects after first paint — wait before declaring missing
      const eth = await waitForProviderQuiet(5000);
      if (cancelled) return;
      if (!eth) {
        setStreamLog((s) => [
          "MetaMask не найден. Откройте эту страницу в Chrome/Edge с расширением (не Cursor Browser). MetaMask = только ETH-вывод, не TON.",
          ...s,
        ].slice(0, 40));
        return;
      }
      window.setTimeout(() => {
        if (!cancelled) void connectAndScan();
      }, 300);
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]);

  useEffect(() => {
    if (!autoPoll) return;
    const id = window.setInterval(() => {
      void runConfiguredAudit({ withBtc: true, quiet: true });
    }, TREASURY_POLL_MS);
    return () => window.clearInterval(id);
  }, [autoPoll, runConfiguredAudit]);

  // WebSocket — только по флагу liveFeed (по умолчанию выкл.)
  useEffect(() => {
    if (!liveFeed) {
      stream.stop();
      setWsOk(false);
      return;
    }
    const scheduleAudit = (withBtc: boolean) => {
      const now = Date.now();
      if (now - lastStreamAudit.current < 30_000) return;
      lastStreamAudit.current = now;
      void runConfiguredAudit({ withBtc, quiet: true });
    };
    const off = stream.onEvent((ev: StreamEvent) => {
      if (ev.kind === "status") {
        setWsOk(ev.ok);
        setStreamLog((s) => [ev.message, ...s].slice(0, 40));
      } else if (ev.kind === "btc_tx") {
        setStreamLog((s) => [`BTC ${ev.address.slice(0, 10)}… tx ${ev.txid}`, ...s].slice(0, 40));
        scheduleAudit(true);
      } else if (ev.kind === "eth_activity") {
        setStreamLog((s) => [
          `ETH ${ev.address.slice(0, 10)}… блок ${ev.blockNumber} bal=${ev.balanceEth}`,
          ...s,
        ].slice(0, 40));
        scheduleAudit(false);
      }
    });
    void stream.start(parseExtra(), []);
    return () => {
      off();
      stream.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [liveFeed]);

  const askBroadcast = (asset: ChainAsset) => {
    setErr(null);
    if (!vault.trim()) {
      setErr("Укажите адрес корпоративного Vault (которым вы владеете).");
      return;
    }
    if (!asset.canSignWithExtension) {
      setErr("Адрес только для чтения. Переключите MetaMask на этот аккаунт и нажмите «Подключить кошелёк».");
      return;
    }
    setPendingAsset(asset);
    setConfirmOpen(true);
  };

  const doBroadcast = async () => {
    if (!pendingAsset) return;
    setConfirmOpen(false);
    setBusy(true);
    setErr(null);
    try {
      const hash = await engine.requestExtensionBroadcast(vault.trim(), pendingAsset);
      setTxHash(hash);
      await connectAndScan();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка отправки");
      refreshLogs();
    } finally {
      setBusy(false);
      setPendingAsset(null);
    }
  };

  const doBatch = async () => {
    setBatchConfirm(false);
    setBusy(true);
    setErr(null);
    try {
      const result = await engine.batchPrepareAndExecute(vault.trim(), ranked);
      setTxHash(result.hashes.join(", "));
      if (result.skipped.length) {
        setErr(
          `Пакет: отправлено ${result.hashes.length}. Пропущено (только чтение): ${result.skipped.length} — переключите аккаунт в MetaMask.`,
        );
      }
      await connectAndScan();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка пакетной отправки");
      refreshLogs();
    } finally {
      setBusy(false);
    }
  };

  const doCollectLiquidity = async () => {
    setCollectConfirm(false);
    setBusy(true);
    setErr(null);
    try {
      const result = await engine.batchCollectProfitableLiquidity(vault.trim(), ranked, {
        includeMarginal,
      });
      setTxHash(result.hashes.join(", "));
      if (result.skipped.length) {
        setErr(
          `Сбор: отправлено ${result.hashes.length}. Пропущено (только чтение): ${result.skipped.length} — смените аккаунт в MetaMask.`,
        );
      }
      await connectAndScan();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Ошибка сбора ликвидности");
      refreshLogs();
    } finally {
      setBusy(false);
    }
  };

  const profitableCount = buckets.profitable.length + (includeMarginal ? buckets.marginal.length : 0);
  const signableProfitable = [...buckets.profitable, ...(includeMarginal ? buckets.marginal : [])].filter(
    (a) => a.canSignWithExtension && a.isProfitableToSweep,
  );

  const hasSignableOnScan = ranked.some((a) => a.canSignWithExtension);
  const walletUi = !connected
    ? {
        tone: "zinc" as const,
        title: "Кошелёк не подключён",
        hint: "Нажмите «Подключить кошелёк» (MetaMask / Rabby).",
      }
    : hasSignableOnScan
      ? {
          tone: "emerald" as const,
          title: "Кошелёк совпадает с адресом скана",
          hint: "Можно подписывать вывод с текущего аккаунта MetaMask.",
        }
      : {
          tone: "amber" as const,
          title: "Аккаунт MetaMask не совпадает с целями скана",
          hint:
            "Активный адрес в расширении не совпадает с найденными балансами. Переключите аккаунт в MetaMask на нужный и снова нажмите «Подключить кошелёк».",
        };

  const gasColor =
    gas?.window === "low"
      ? "text-emerald-400"
      : gas?.window === "normal"
        ? "text-cyan-300"
        : gas?.window === "elevated"
          ? "text-amber-300"
          : gas?.window === "high"
            ? "text-rose-400"
            : "text-zinc-400";

  return (
    <section className="rounded-xl border border-cyan-900/50 bg-zinc-950/90 p-4 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-cyan-400">Живой аудит ликвидности (ETH + BTC)</h2>
          <p className="mt-1 text-xs text-zinc-400">
            Сортировка по ликвидности · поток mempool · уведомления · пакетный вывод только с{" "}
            <strong className="text-zinc-200">подключённого</strong> аккаунта MetaMask.
            MetaMask <span className="text-amber-200">не</span> подписывает TON/VCORE Genesis — только ETH.
            Если кнопка не работает: Chrome/Edge + расширение, сайт в Connected sites, не Cursor Browser.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1 text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${netOk ? "bg-emerald-400 animate-pulse" : netOk === false ? "bg-rose-500" : "bg-zinc-600"}`}
            />
            <span className="text-zinc-400">RPC {netMeta}</span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${wsOk ? "bg-cyan-400 animate-pulse" : wsOk === false ? "bg-amber-500" : "bg-zinc-600"}`}
            />
            <span className="text-zinc-400">
              WS {wsOk == null ? "…" : wsOk ? "онлайн" : "выкл"} · опрос {lastPoll}
            </span>
          </div>
        </div>
      </div>

      {/* Как устроен поиск / вывод */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-900/70 p-4 text-xs text-zinc-300 space-y-2">
        <p className="font-semibold text-cyan-300">Туннель ликвидности (схема)</p>
        <ol className="list-decimal space-y-1 pl-4 text-zinc-400">
          <li>
            <strong className="text-zinc-200">Скан</strong> — публичные API по вашим адресам.
          </li>
          <li>
            <strong className="text-zinc-200">Profit engine</strong> — net после комиссии; убыточное → SKIP.
          </li>
          <li>
            <strong className="text-zinc-200">HITL</strong> — BTC: y/N в терминале · ETH: MetaMask.
          </li>
          <li>
            <strong className="text-zinc-200">Vault</strong> — ваш локальный / корпоративный адрес.
          </li>
        </ol>
        <p className="text-[11px] text-zinc-500">
          Агент: <code className="text-amber-200/90">npm run agent:sweep</code> · env:{" "}
          <code>scripts/env.btc.example</code>
        </p>
      </div>

      {/* Статус кошелька */}
      <div
        className={`rounded-xl border p-3 ${
          walletUi.tone === "emerald"
            ? "border-emerald-700 bg-emerald-950/40"
            : walletUi.tone === "amber"
              ? "border-amber-600 bg-amber-950/50"
              : "border-zinc-700 bg-zinc-900/80"
        }`}
      >
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`h-3 w-3 shrink-0 rounded-full ${
              walletUi.tone === "emerald"
                ? "bg-emerald-400 animate-pulse"
                : walletUi.tone === "amber"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-zinc-500"
            }`}
          />
          <div className="min-w-0 flex-1">
            <p
              className={`text-sm font-semibold ${
                walletUi.tone === "emerald"
                  ? "text-emerald-300"
                  : walletUi.tone === "amber"
                    ? "text-amber-200"
                    : "text-zinc-300"
              }`}
            >
              {walletUi.title}
            </p>
            <p className="mt-0.5 text-[11px] text-zinc-400">{walletUi.hint}</p>
            {connected && (
              <p className="mt-1 truncate font-mono text-[11px] text-cyan-300/90">Активный: {connected}</p>
            )}
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void connectAndScan()}
            className="rounded-lg bg-cyan-600 px-3 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          >
            {connected ? "Обновить подключение" : "Подключить кошелёк"}
          </button>
        </div>
      </div>

      {err && <div className="rounded-lg border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">{err}</div>}
      {txHash && (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/30 px-3 py-2 text-xs text-emerald-300 break-all">
          Транзакция: {txHash}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-xs">
          <div className="font-semibold text-zinc-300">Окно газа ETH</div>
          {gas ? (
            <>
              <p className={`mt-1 font-mono ${gasColor}`}>
                {gasWindowRu(gas.window)} · ≈{gas.maxFeeGwei} gwei
              </p>
              <p className="mt-1 text-zinc-400">{gas.suggestion}</p>
            </>
          ) : (
            <p className="mt-1 text-zinc-500">Загрузка…</p>
          )}
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-xs">
          <div className="font-semibold text-zinc-300">Комиссии BTC</div>
          {btcFees ? (
            <p className="mt-1 font-mono text-cyan-300">
              быстро {btcFees.fastestFee} · эконом {btcFees.economyFee} sat/vB — {btcFees.suggestion}
            </p>
          ) : (
            <p className="mt-1 text-zinc-500">Загрузка…</p>
          )}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="text-[10px] uppercase text-zinc-500">Корпоративный Vault (ETH)</label>
          <input
            value={vault}
            onChange={(e) => setVault(e.target.value)}
            placeholder="0x… ваш Vault"
            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-emerald-300"
          />
        </div>
        <div>
          <label className="text-[10px] uppercase text-zinc-500">Доп. свои адреса ETH</label>
          <textarea
            value={extraList}
            onChange={(e) => setExtraList(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs"
            placeholder="0x…"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void runConfiguredAudit({ withBtc: true })}
          className="rounded-lg bg-cyan-700 px-3 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
        >
          Обновить скан
        </button>
        <button
          type="button"
          disabled={busy || !vault.trim()}
          onClick={() => {
            if (!vault.trim()) {
              setErr("Сначала укажите Vault.");
              return;
            }
            setBatchConfirm(true);
          }}
          className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-zinc-950 disabled:opacity-50"
          title="Только балансы текущего аккаунта MetaMask"
        >
          Пакет → Vault (подписанные)
        </button>
        <label className="flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-2 text-xs">
          <input type="checkbox" checked={autoPoll} onChange={(e) => setAutoPoll(e.target.checked)} />
          Автообновление
        </label>
        <label className="flex items-center gap-2 rounded-lg border border-zinc-700 px-3 py-2 text-xs">
          <input type="checkbox" checked={liveFeed} onChange={(e) => setLiveFeed(e.target.checked)} />
          Live WS
        </label>
        <button
          type="button"
          className="rounded-lg border border-zinc-600 px-3 py-2 text-xs"
          onClick={() => exportLiquidityJson({ ethAssets: ranked, btcAudits, logs, gas })}
        >
          JSON
        </button>
        <button
          type="button"
          className="rounded-lg border border-zinc-600 px-3 py-2 text-xs"
          onClick={() => exportLiquidityCsv(ranked, btcAudits)}
        >
          CSV
        </button>
        <button type="button" className="rounded-lg border border-zinc-600 px-3 py-2 text-xs" onClick={() => exportLogsCsv(logs)}>
          Лог CSV
        </button>
      </div>

      {/* Контрастный блок пыли / выгодных остатков + кнопка сбора */}
      <section className="rounded-2xl border-2 border-amber-500/80 bg-gradient-to-b from-amber-950/50 to-zinc-950 p-4 shadow-[0_0_40px_-12px_rgba(245,158,11,0.45)] space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-amber-200">Пыль и выгодные остатки</h3>
            <p className="mt-1 text-[11px] text-amber-100/80 max-w-xl">
              Автофильтр рентабельности: сравниваем баланс с текущей оценкой газа. Выводим только то, что{" "}
              <strong>оставляет положительный net</strong> после комиссии.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] font-mono">
            <span className="rounded-md border-2 border-emerald-500 bg-emerald-950/60 px-2.5 py-1 font-semibold text-emerald-300">
              Выгодный {buckets.profitable.length}
            </span>
            <span className="rounded-md border-2 border-amber-400 bg-amber-950/60 px-2.5 py-1 font-semibold text-amber-200">
              Пограничный {buckets.marginal.length}
            </span>
            <span className="rounded-md border-2 border-rose-500 bg-rose-950/50 px-2.5 py-1 font-semibold text-rose-300">
              Пыль {buckets.dust.length}
            </span>
            <span className="rounded-md border-2 border-zinc-500 bg-zinc-900 px-2.5 py-1 text-zinc-300">
              Аномалия {buckets.anomalies.length}
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-cyan-800/60 bg-cyan-950/30 p-3 space-y-2">
          <p className="text-sm font-semibold text-cyan-200">Пакетный сбор ликвидности на Vault</p>
          <p className="text-[11px] leading-relaxed text-zinc-300">
            Кнопка ниже готовит переводы <strong className="text-zinc-100">только с аккаунта, который сейчас
            активен в MetaMask</strong>. Каждый шаг потребует подтверждения в расширении. Адреса из списка скана,
            которые не совпадают с активным аккаунтом, будут пропущены (безопасность: без серверных ключей).
            Укажите Vault выше, подключите нужный аккаунт, затем соберите выгодные остатки.
          </p>
          <label className="flex items-center gap-2 text-xs text-zinc-300">
            <input
              type="checkbox"
              checked={includeMarginal}
              onChange={(e) => setIncludeMarginal(e.target.checked)}
            />
            Включить пограничные (тонкая маржа) в сбор
          </label>
          <button
            type="button"
            disabled={busy || !vault.trim() || profitableCount === 0}
            onClick={() => {
              if (!vault.trim()) {
                setErr("Сначала укажите адрес корпоративного Vault.");
                return;
              }
              setCollectConfirm(true);
            }}
            className="w-full rounded-xl bg-amber-500 py-3.5 text-sm font-extrabold tracking-wide text-zinc-950 shadow-lg shadow-amber-900/40 disabled:opacity-40 hover:bg-amber-400"
          >
            Пакетный сбор выгодной ликвидности → Vault
            {signableProfitable.length > 0
              ? ` · сейчас подписываемых: ${signableProfitable.length}`
              : " · сначала подключите совпадающий аккаунт"}
          </button>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wide text-emerald-400">
              Кандидаты на вывод (net &gt; 0)
            </h4>
            {[...buckets.profitable, ...buckets.marginal].length === 0 ? (
              <p className="rounded-lg border border-zinc-700 bg-zinc-950/80 p-3 text-xs text-zinc-500">
                Пока нет — добавьте свои адреса и обновите скан.
              </p>
            ) : (
              [...buckets.profitable, ...buckets.marginal].map((a) => (
                <div
                  key={a.id}
                  className={`rounded-lg border-2 p-3 text-xs space-y-1 ${
                    a.dustClass === "profitable"
                      ? "border-emerald-500/70 bg-emerald-950/40"
                      : "border-amber-500/70 bg-amber-950/35"
                  }`}
                  title={DUST_TIP_RU[a.dustClass]}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-bold text-emerald-300">{a.balanceDecimal} ETH</span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                        a.dustClass === "profitable" ? "bg-emerald-800 text-emerald-100" : "bg-amber-800 text-amber-100"
                      }`}
                    >
                      {dustClassLabel(a.dustClass)}
                    </span>
                  </div>
                  <p className="text-zinc-300">
                    Чистыми после газа ≈ <strong>{a.netAfterGasEth.toFixed(6)}</strong> ETH
                  </p>
                  <p className="truncate font-mono text-[10px] text-zinc-500">{a.address}</p>
                  <p className="rounded bg-black/30 px-2 py-1.5 text-[10px] leading-snug text-zinc-400">
                    {DUST_TIP_RU[a.dustClass]}
                  </p>
                  <p className="text-[10px] text-zinc-600">{a.dustNote}</p>
                </div>
              ))
            )}
          </div>
          <div className="space-y-2">
            <h4 className="text-[10px] font-bold uppercase tracking-wide text-rose-400">
              Пыль / аномалии (не выводить отдельно)
            </h4>
            {[...buckets.dust, ...buckets.anomalies].length === 0 ? (
              <p className="rounded-lg border border-zinc-700 bg-zinc-950/80 p-3 text-xs text-zinc-500">
                Нерентабельной пыли нет.
              </p>
            ) : (
              [...buckets.dust, ...buckets.anomalies].map((a) => (
                <div
                  key={a.id}
                  className="rounded-lg border-2 border-rose-600/60 bg-rose-950/35 p-3 text-xs space-y-1"
                  title={DUST_TIP_RU[a.dustClass]}
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-bold text-rose-300">{a.balanceDecimal} ETH</span>
                    <span className="rounded bg-rose-900 px-1.5 py-0.5 text-[10px] font-bold text-rose-100">
                      {dustClassLabel(a.dustClass)}
                    </span>
                  </div>
                  <p className="text-zinc-400">
                    Net ≈ {a.netAfterGasEth.toFixed(6)} (убыток / слишком тонко)
                  </p>
                  <p className="truncate font-mono text-[10px] text-zinc-600">{a.address}</p>
                  <p className="rounded bg-black/30 px-2 py-1.5 text-[10px] leading-snug text-zinc-400">
                    {DUST_TIP_RU[a.dustClass]}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-2 lg:col-span-1">
          <h3 className="text-xs font-semibold uppercase text-zinc-400">ETH (по приоритету)</h3>
          {ranked.length === 0 ? (
            <p className="rounded-lg border border-zinc-800 p-3 text-center text-xs text-zinc-500">Нет балансов</p>
          ) : (
            ranked.map((asset, i) => (
              <div key={asset.id} className="rounded-lg border border-zinc-800 p-3 text-xs space-y-1">
                <div className="flex justify-between text-zinc-500">
                  <span>
                    #{i + 1} · {rankReasonRu(asset.rankReason)}
                  </span>
                  <span>{asset.canSignWithExtension ? "ПОДПИСЬ" : "ТОЛЬКО ЧТЕНИЕ"}</span>
                </div>
                <div className="font-bold text-emerald-400">{asset.balanceDecimal} ETH</div>
                <p className="text-[10px] text-zinc-500">
                  {dustClassLabel(asset.dustClass)} · net ≈ {asset.netAfterGasEth.toFixed(6)}
                </p>
                <p className="truncate font-mono text-zinc-500">{asset.address}</p>
                <button
                  type="button"
                  disabled={busy || !asset.canSignWithExtension}
                  onClick={() => askBroadcast(asset)}
                  className="w-full rounded bg-emerald-600 py-1.5 text-[11px] font-bold text-zinc-950 disabled:opacity-40"
                >
                  {asset.canSignWithExtension ? "Отправить на Vault" : "Смените аккаунт в MetaMask"}
                </button>
              </div>
            ))
          )}
          <h3 className="pt-2 text-xs font-semibold uppercase text-zinc-400">BTC (аудит)</h3>
          {btcAudits.length === 0 && (
            <p className="rounded-lg border border-zinc-800 p-2 text-xs text-zinc-500">Нет BTC-целей в конфиге</p>
          )}
          {btcAudits.map((b) => (
            <div key={b.address} className="rounded-lg border border-zinc-800 p-3 text-xs">
              <div className="font-bold text-amber-300">
                {b.balanceBtc} BTC · {b.utxoCount} UTXO
              </div>
              <p className="truncate font-mono text-zinc-500">{b.address}</p>
              <p className="mt-1 text-[10px] text-zinc-500">
                Вывод BTC: в корне репо <code className="text-amber-200/90">npm run btc:sweep</code> (ключи в
                .env.btc). Сервер не подписывает.
              </p>
            </div>
          ))}
        </div>
        <div>
          <h3 className="text-xs font-semibold uppercase text-zinc-400">Живой поток</h3>
          <div className="mt-2 max-h-72 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-[11px] space-y-1">
            {streamLog.length === 0 && <p className="text-zinc-600">Ожидание событий WebSocket…</p>}
            {streamLog.map((l, i) => (
              <div key={`${l}-${i}`} className="text-cyan-300/90">
                {l}
              </div>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-xs font-semibold uppercase text-zinc-400">Системный журнал</h3>
          <div className="mt-2 max-h-72 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 p-3 font-mono text-[11px] space-y-1">
            {logs.map((l) => (
              <div key={l.id}>
                <span className="text-zinc-600">[{l.timestamp}]</span>{" "}
                <span
                  className={
                    l.level === "ERROR"
                      ? "text-rose-400"
                      : l.level === "SUCCESS"
                        ? "text-emerald-400"
                        : "text-zinc-300"
                  }
                >
                  {l.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {confirmOpen && pendingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-950 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-emerald-400">Подтвердить перевод</h3>
            <p className="break-all font-mono text-[11px] text-cyan-300">Откуда {pendingAsset.address}</p>
            <p className="break-all font-mono text-[11px] text-emerald-300">Куда {vault.trim()}</p>
            <p className="text-[11px] text-zinc-400">Откроется окно MetaMask для вашей подписи.</p>
            <div className="flex gap-2">
              <button
                type="button"
                className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-bold text-zinc-950"
                onClick={() => void doBroadcast()}
              >
                Открыть кошелёк
              </button>
              <button
                type="button"
                className="flex-1 rounded-lg border border-zinc-600 py-2 text-xs"
                onClick={() => {
                  setConfirmOpen(false);
                  setPendingAsset(null);
                }}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {batchConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-950 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-emerald-400">Пакет → Vault</h3>
            <p className="text-xs text-zinc-400">
              Только балансы <strong className="text-zinc-200">текущего</strong> аккаунта MetaMask. Каждый перевод —
              отдельное подтверждение. Остальные адреса списка пропускаются.
            </p>
            <p className="text-xs text-zinc-500">
              Сейчас подписываемых: {ranked.filter((a) => a.canSignWithExtension).length} · только чтение:{" "}
              {ranked.filter((a) => !a.canSignWithExtension).length}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-bold text-zinc-950"
                onClick={() => void doBatch()}
              >
                Запустить пакет
              </button>
              <button
                type="button"
                className="flex-1 rounded-lg border border-zinc-600 py-2 text-xs"
                onClick={() => setBatchConfirm(false)}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {collectConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-amber-800 bg-zinc-950 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-amber-300">Сбор выгодной ликвидности</h3>
            <p className="text-xs text-zinc-400">
              Переводим остатки, где <strong className="text-zinc-200">баланс &gt; текущий газ</strong>
              {includeMarginal ? " (включая пограничные)" : ""}. Подпись — только через подключённый MetaMask.
            </p>
            <p className="break-all font-mono text-[11px] text-emerald-300">Vault: {vault.trim()}</p>
            <p className="text-xs text-zinc-500">
              Кандидатов: {profitableCount} · подписываемых сейчас: {signableProfitable.length}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="flex-1 rounded-lg bg-amber-600 py-2 text-xs font-bold text-zinc-950"
                onClick={() => void doCollectLiquidity()}
              >
                Открыть MetaMask
              </button>
              <button
                type="button"
                className="flex-1 rounded-lg border border-zinc-600 py-2 text-xs"
                onClick={() => setCollectConfirm(false)}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
