/**
 * Secure Web3 adapter — OWN wallets via browser extension.
 * - scanTargetAddresses: READ-ONLY public balances for addresses YOU provide
 * - broadcast: ONLY from the connected MetaMask/Rabby account (signer must match asset)
 * NEVER accepts raw private keys.
 */
import { ethers } from "ethers";
import { resolveEthAuditTargets } from "../../config/treasuryTargets";
import { fetchGasAdvice, type GasAdvice } from "./gasOptimizer";

export type DustClass = "profitable" | "marginal" | "dust" | "anomaly";

export interface ChainAsset {
  id: string;
  address: string;
  balanceWei: string;
  balanceDecimal: number;
  symbol: string;
  estimatedGasWei: string;
  /** balance ≤ ~2× gas → uneconomic alone / dust band */
  isDust: boolean;
  /** balance > gas cost → sweep leaves positive net */
  isProfitableToSweep: boolean;
  /** net wei after estimated gas (can be negative) */
  netAfterGasWei: string;
  netAfterGasEth: number;
  dustClass: DustClass;
  dustNote: string;
  /** true only when this address is the currently connected extension account */
  canSignWithExtension?: boolean;
}

export interface SweepBuckets {
  profitable: ChainAsset[];
  dust: ChainAsset[];
  anomalies: ChainAsset[];
  marginal: ChainAsset[];
}

/** Alias kept for callers expecting TreasuryLog name */
export type TreasuryLog = Web3TreasuryLog;

export interface Web3TreasuryLog {
  id: string;
  timestamp: string;
  level: "INFO" | "SUCCESS" | "ERROR" | "BROADCAST";
  message: string;
}

type EthereumProvider = {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  isMetaMask?: boolean;
  isRabby?: boolean;
  providers?: EthereumProvider[];
};

/**
 * Resolve a browser wallet. Multiple extensions often share window.ethereum;
 * prefer MetaMask, then Rabby, then the top-level provider.
 */
function ethereum(): EthereumProvider | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    ethereum?: EthereumProvider;
    rabby?: EthereumProvider;
  };
  const root = w.ethereum;
  if (!root) return null;
  const list = Array.isArray(root.providers) && root.providers.length > 0 ? root.providers : [root];
  const metamask = list.find((p) => p?.isMetaMask && !p?.isRabby);
  if (metamask) return metamask;
  const rabby = list.find((p) => p?.isRabby) || w.rabby;
  if (rabby) return rabby;
  return root;
}

async function waitForEthereum(ms = 4000): Promise<EthereumProvider | null> {
  const started = Date.now();
  let eth = ethereum();
  while (!eth && Date.now() - started < ms) {
    await new Promise((r) => setTimeout(r, 200));
    eth = ethereum();
  }
  return eth;
}

/** Exported for UI — detect extension without throwing. */
export async function waitForProviderQuiet(ms = 4000): Promise<boolean> {
  return !!(await waitForEthereum(ms));
}

export class SecureWeb3TreasuryEngine {
  private logs: Web3TreasuryLog[] = [];
  private connectedAddress: string | null = null;

  private addLog(level: Web3TreasuryLog["level"], message: string) {
    this.logs.unshift({
      id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toLocaleTimeString(),
      level,
      message,
    });
    this.logs = this.logs.slice(0, 80);
  }

  getLogs(): Web3TreasuryLog[] {
    return [...this.logs];
  }

  /** Env NEXT_PUBLIC_AUDIT_TARGETS + app/config/treasuryTargets.ts + optional extras. */
  loadConfiguredTargets(extra: string[] = []): string[] {
    return resolveEthAuditTargets(extra);
  }

  async scanConfiguredTargets(extra: string[] = []): Promise<ChainAsset[]> {
    const targets = this.loadConfiguredTargets(extra);
    if (targets.length === 0) {
      this.addLog("INFO", "No ETH audit targets configured (NEXT_PUBLIC_AUDIT_TARGETS / treasuryTargets.ts).");
      return [];
    }
    return this.scanTargetAddresses(targets);
  }

  async sampleGasAdvice(): Promise<GasAdvice> {
    const provider = await this.readProvider();
    const advice = await fetchGasAdvice(provider);
    this.addLog("INFO", `Gas window=${advice.window} maxFee≈${advice.maxFeeGwei} gwei`);
    return advice;
  }

  async pingNetwork(): Promise<{ ok: boolean; blockNumber: number | null; latencyMs: number; rpc: string }> {
    const started = performance.now();
    try {
      const provider = await this.readProvider();
      const blockNumber = await this.withTimeout(provider.getBlockNumber(), 12_000, "RPC getBlockNumber");
      const latencyMs = Math.round(performance.now() - started);
      const rpc = ethereum() ? "browser-wallet" : process.env.NEXT_PUBLIC_RPC_URL || "public-rpc";
      this.addLog("INFO", `RPC ok · блок ${blockNumber} · ${latencyMs}мс`);
      return { ok: true, blockNumber, latencyMs, rpc };
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      this.addLog("ERROR", `RPC ping: ${msg}`);
      return { ok: false, blockNumber: null, latencyMs: Math.round(performance.now() - started), rpc: "error" };
    }
  }

  private requireExtension(): EthereumProvider {
    const eth = ethereum();
    if (!eth) {
      throw new Error(
        "MetaMask/Rabby не найден в этом браузере (window.ethereum пуст). " +
          "Откройте /treasury в Chrome/Edge с установленным MetaMask — не во встроенном браузере Cursor. " +
          "MetaMask не подписывает TON Genesis — только ETH-вывод.",
      );
    }
    return eth;
  }

  private browserProvider(): ethers.BrowserProvider {
    return new ethers.BrowserProvider(this.requireExtension());
  }

  /** Read provider: extension if present, else public RPC (read-only). */
  private async readProvider(): Promise<ethers.Provider> {
    if (ethereum()) {
      const p = this.browserProvider();
      // короткий ping с таймаутом — иначе вкладка «висит» на MetaMask
      await Promise.race([
        p.getBlockNumber(),
        new Promise((_, rej) => setTimeout(() => rej(new Error("Таймаут RPC MetaMask (12с)")), 12_000)),
      ]).catch(() => undefined);
      return p;
    }
    const url = process.env.NEXT_PUBLIC_RPC_URL || "https://eth.llamarpc.com";
    const p = new ethers.JsonRpcProvider(url, undefined, { staticNetwork: true });
    return p;
  }

  private withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
    return Promise.race([
      p,
      new Promise<T>((_, rej) => setTimeout(() => rej(new Error(`${label} — таймаут ${ms}мс`)), ms)),
    ]);
  }

  /**
   * Dust / profitability gate from live fee data.
   * profitable = balance > gas · dust = balance ≤ gas · marginal = gas < bal ≤ 2×gas · anomaly = tiny residual
   */
  classifyAssetEconomics(balanceWei: bigint, estimatedGasWei: bigint): {
    isDust: boolean;
    isProfitableToSweep: boolean;
    netAfterGasWei: bigint;
    netAfterGasEth: number;
    dustClass: DustClass;
    dustNote: string;
  } {
    const net = balanceWei - estimatedGasWei;
    const isProfitableToSweep = balanceWei > estimatedGasWei;
    const isDust = balanceWei <= estimatedGasWei * BigInt(2);
    let dustClass: DustClass;
    let dustNote: string;
    if (balanceWei <= BigInt(0)) {
      dustClass = "anomaly";
      dustNote = "Пустой баланс после скана — игнорировать.";
    } else if (balanceWei < estimatedGasWei / BigInt(10) && balanceWei > BigInt(0)) {
      dustClass = "anomaly";
      dustNote = "Аномалия: остаток сильно ниже газа — оставить или ждать дешёвый газ.";
    } else if (!isProfitableToSweep) {
      dustClass = "dust";
      dustNote = "Пыль: баланс ≤ газа — одиночный вывод убыточен.";
    } else if (isDust) {
      dustClass = "marginal";
      dustNote = "Пограничный: выгодно, но тонкая маржа (≤2× газа) — лучше при низком газе.";
    } else {
      dustClass = "profitable";
      dustNote = "Выгодный: баланс > газа — после перевода останется чистый остаток.";
    }
    return {
      isDust,
      isProfitableToSweep,
      netAfterGasWei: net,
      netAfterGasEth: parseFloat(ethers.formatEther(net)),
      dustClass,
      dustNote,
    };
  }

  /** Split scanned assets into dust / profitable / anomaly buckets for the audit panel. */
  filterSweepBuckets(assets: ChainAsset[]): SweepBuckets {
    const buckets: SweepBuckets = { profitable: [], dust: [], anomalies: [], marginal: [] };
    for (const a of assets) {
      if (a.dustClass === "profitable") buckets.profitable.push(a);
      else if (a.dustClass === "marginal") buckets.marginal.push(a);
      else if (a.dustClass === "anomaly") buckets.anomalies.push(a);
      else buckets.dust.push(a);
    }
    const byNet = (x: ChainAsset, y: ChainAsset) => {
      const dx = BigInt(x.netAfterGasWei);
      const dy = BigInt(y.netAfterGasWei);
      if (dy === dx) return 0;
      return dy > dx ? -1 : 1;
    };
    buckets.profitable.sort(byNet);
    buckets.marginal.sort(byNet);
    buckets.dust.sort(byNet);
    buckets.anomalies.sort(byNet);
    return buckets;
  }

  /**
   * Multi-target READ audit for addresses you supply (own hot/cold/ops wallets).
   * Does not unlock spend for foreign addresses — only canSignWithExtension on connected account.
   */
  async scanTargetAddresses(targetAddresses: string[]): Promise<ChainAsset[]> {
    this.addLog("INFO", `Multi-target balance audit: ${targetAddresses.length} address(es)…`);
    const provider = await this.readProvider();
    const feeData = await provider.getFeeData();
    const maxFee = feeData.maxFeePerGas ?? feeData.gasPrice ?? ethers.parseUnits("20", "gwei");
    const estimatedGasWei = maxFee * BigInt(21000);
    const connected = this.connectedAddress?.toLowerCase() ?? null;
    const discovered: ChainAsset[] = [];

    for (const address of targetAddresses) {
      try {
        const cleanAddr = address.trim();
        if (!ethers.isAddress(cleanAddr)) continue;

        const balanceWei = await this.withTimeout(
          provider.getBalance(cleanAddr),
          12_000,
          `getBalance ${cleanAddr.slice(0, 10)}`,
        );
        if (balanceWei <= BigInt(0)) continue;

        const balanceDecimal = parseFloat(ethers.formatEther(balanceWei));
        const eco = this.classifyAssetEconomics(balanceWei, estimatedGasWei);
        const canSign = !!connected && cleanAddr.toLowerCase() === connected;

        discovered.push({
          id: `ast_${cleanAddr}_${Date.now()}`,
          address: cleanAddr,
          balanceWei: balanceWei.toString(),
          balanceDecimal,
          symbol: "ETH",
          estimatedGasWei: estimatedGasWei.toString(),
          isDust: eco.isDust,
          isProfitableToSweep: eco.isProfitableToSweep,
          netAfterGasWei: eco.netAfterGasWei.toString(),
          netAfterGasEth: eco.netAfterGasEth,
          dustClass: eco.dustClass,
          dustNote: eco.dustNote,
          canSignWithExtension: canSign,
        });
        this.addLog(
          "SUCCESS",
          `${eco.dustClass.toUpperCase()} ${cleanAddr.slice(0, 8)}…: ${balanceDecimal} ETH · net≈${eco.netAfterGasEth.toFixed(6)}${canSign ? " (signable)" : " (read-only)"}`,
        );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        this.addLog("ERROR", `Audit failed for ${address}: ${msg}`);
      }
    }

    if (discovered.length === 0) {
      this.addLog("INFO", "Scan done — no non-zero balances in the provided list.");
    } else {
      const b = this.filterSweepBuckets(discovered);
      this.addLog(
        "INFO",
        `Dust filter: profitable ${b.profitable.length} · marginal ${b.marginal.length} · dust ${b.dust.length} · anomaly ${b.anomalies.length}`,
      );
    }
    return discovered;
  }

  /**
   * Batch collect profitable (+ optional marginal) remnants to vault via MetaMask.
   * Signable only — same honesty as batchPrepareAndExecute.
   */
  async batchCollectProfitableLiquidity(
    destinationAddress: string,
    assets: ChainAsset[],
    opts?: { includeMarginal?: boolean },
  ): Promise<{ hashes: string[]; skipped: string[]; prepared: number }> {
    const buckets = this.filterSweepBuckets(assets);
    const pool = [
      ...buckets.profitable,
      ...(opts?.includeMarginal ? buckets.marginal : []),
    ].filter((a) => a.isProfitableToSweep);
    this.addLog(
      "INFO",
      `Liquidity collect: ${pool.length} profitable remnant(s)${opts?.includeMarginal ? " (+marginal)" : ""}.`,
    );
    return this.batchPrepareAndExecute(destinationAddress, pool);
  }

  async scanConnectedWallet(extraTargets: string[] = []): Promise<{ address: string; assets: ChainAsset[] }> {
    const eth = (await waitForEthereum(5000)) || this.requireExtension();
    this.addLog("INFO", "Запрос eth_requestAccounts (откройте всплывающее окно MetaMask)…");
    let accounts: string[];
    try {
      accounts = (await eth.request({ method: "eth_requestAccounts" })) as string[];
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      const code = typeof e === "object" && e && "code" in e ? Number((e as { code: number }).code) : 0;
      if (code === 4001 || /user rejected|denied/i.test(msg)) {
        throw new Error("Подключение отклонено в MetaMask. Нажмите «Подключить кошелёк» и подтвердите запрос.");
      }
      if (code === -32002) {
        throw new Error("Уже есть незакрытый запрос MetaMask — откройте расширение и подтвердите/закройте его.");
      }
      throw new Error(`MetaMask: ${msg}`);
    }
    const address = accounts[0];
    if (!address || !ethers.isAddress(address)) {
      throw new Error("Кошелёк не вернул адрес. Разблокируйте MetaMask и повторите.");
    }
    this.connectedAddress = address;

    // Ensure we can get a signer (some embeds expose ethereum but block signing)
    try {
      const bp = new ethers.BrowserProvider(eth);
      await this.withTimeout(bp.getSigner(), 15_000, "MetaMask getSigner");
    } catch (e) {
      throw new Error(
        `Подключение есть, но подпись недоступна: ${e instanceof Error ? e.message : String(e)}. ` +
          "Проверьте, что сайт разрешён в MetaMask → Connected sites.",
      );
    }

    const targets = [address, ...extraTargets.filter((a) => a.trim().toLowerCase() !== address.toLowerCase())];
    const assets = await this.scanTargetAddresses(targets);
    this.addLog("SUCCESS", `Connected ${address}`);
    return { address, assets };
  }

  /**
   * Send ETH from the CONNECTED extension account to your vault.
   * Refuses if asset.address ≠ connected signer (cannot spend other scanned balances).
   */
  async requestExtensionBroadcast(destinationAddress: string, asset: ChainAsset): Promise<string> {
    if (!ethers.isAddress(destinationAddress)) {
      throw new Error("Destination vault is not a valid address.");
    }
    if (destinationAddress.toLowerCase() === asset.address.toLowerCase()) {
      throw new Error("Destination must differ from the source wallet.");
    }

    this.addLog("BROADCAST", `Wallet popup: settle to vault ${destinationAddress}`);
    const browserProvider = this.browserProvider();
    const signer = await browserProvider.getSigner();
    const signerAddr = await signer.getAddress();

    if (signerAddr.toLowerCase() !== asset.address.toLowerCase()) {
      throw new Error(
        "Cannot broadcast this asset: extension signer must match the asset address. " +
          "Read-only audited addresses are not spendable here — switch MetaMask to that account first.",
      );
    }

    const liveBalance = await browserProvider.getBalance(signerAddr);
    const gasLimit = BigInt(21000);
    const feeData = await browserProvider.getFeeData();
    const maxFee = feeData.maxFeePerGas ?? feeData.gasPrice ?? ethers.parseUnits("20", "gwei");
    const totalGasCost = maxFee * gasLimit;

    if (liveBalance <= totalGasCost) {
      throw new Error("Insufficient balance to cover network gas fees.");
    }

    const valueToSend = liveBalance - totalGasCost;
    const txReq: ethers.TransactionRequest = {
      to: destinationAddress,
      value: valueToSend,
      gasLimit,
    };
    if (feeData.maxFeePerGas && feeData.maxPriorityFeePerGas) {
      txReq.maxFeePerGas = feeData.maxFeePerGas;
      txReq.maxPriorityFeePerGas = feeData.maxPriorityFeePerGas;
    } else if (feeData.gasPrice) {
      txReq.gasPrice = feeData.gasPrice;
    }

    const tx = await signer.sendTransaction(txReq);
    this.addLog("SUCCESS", `Settlement broadcast. Hash: ${tx.hash}`);
    return tx.hash;
  }

  /**
   * Sequential extension approvals for SIGNABLE assets only (connected account).
   * Other config addresses stay skipped — EOA multicall cannot spend without their keys.
   */
  async batchPrepareAndExecute(
    destinationAddress: string,
    assets: ChainAsset[],
  ): Promise<{ hashes: string[]; skipped: string[]; prepared: number }> {
    if (!ethers.isAddress(destinationAddress)) {
      throw new Error("Destination vault is not a valid address.");
    }
    const signable = assets.filter((a) => a.canSignWithExtension && BigInt(a.balanceWei) > BigInt(0));
    const skipped = assets.filter((a) => !a.canSignWithExtension).map((a) => a.address);
    this.addLog(
      "INFO",
      `Batch prepare: ${signable.length} signable · ${skipped.length} read-only skipped (switch MetaMask per account).`,
    );
    if (signable.length === 0) {
      throw new Error(
        "No signable assets. Connect the wallet that owns a non-zero target, then run batch again.",
      );
    }
    const hashes: string[] = [];
    for (const asset of signable) {
      this.addLog("BROADCAST", `Batch step → ${asset.address.slice(0, 10)}…`);
      const hash = await this.requestExtensionBroadcast(destinationAddress, asset);
      hashes.push(hash);
    }
    this.addLog("SUCCESS", `Batch done: ${hashes.length} tx(s).`);
    return { hashes, skipped, prepared: signable.length };
  }

  async peekConnectedAddress(): Promise<string | null> {
    const eth = ethereum();
    if (!eth) return null;
    try {
      const accounts = (await eth.request({ method: "eth_accounts" })) as string[];
      return accounts[0] ?? null;
    } catch {
      return null;
    }
  }
}
