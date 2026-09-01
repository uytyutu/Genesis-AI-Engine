/**
 * Bitcoin read-only liquidity audit via mempool.space public API.
 * Tracks addresses YOU configure — no signing / no private keys.
 */
import { resolveBtcAuditTargets } from "../../config/treasuryTargets";

const MEMPOOL_BASE = process.env.NEXT_PUBLIC_MEMPOOL_API || "https://mempool.space/api";

export interface BtcUtxo {
  txid: string;
  vout: number;
  valueSats: number;
  status: { confirmed: boolean; block_height?: number };
}

export interface BtcFeeAdvice {
  fastestFee: number;
  halfHourFee: number;
  hourFee: number;
  economyFee: number;
  minimumFee: number;
  suggestion: string;
  sampledAt: string;
}

export interface BtcAddressAudit {
  address: string;
  balanceSats: number;
  balanceBtc: number;
  utxoCount: number;
  chainTxCount: number;
  mempoolTxCount: number;
  utxos: BtcUtxo[];
  /** Unsigned draft for OWN wallet software — not broadcast by Virtus */
  draftPayload: {
    type: "bitcoin_consolidation_intent";
    inputs: { txid: string; vout: number; valueSats: number }[];
    note: string;
  };
}

export interface BtcEngineLog {
  id: string;
  timestamp: string;
  level: "INFO" | "SUCCESS" | "ERROR";
  message: string;
}

async function mempoolGet<T>(path: string): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15_000);
  try {
    const res = await fetch(`${MEMPOOL_BASE}${path}`, { cache: "no-store", signal: ctrl.signal });
    if (!res.ok) throw new Error(`mempool.space HTTP ${res.status} for ${path}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export class BitcoinTreasuryEngine {
  private logs: BtcEngineLog[] = [];

  private addLog(level: BtcEngineLog["level"], message: string) {
    this.logs.unshift({
      id: `btc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toLocaleTimeString(),
      level,
      message,
    });
    this.logs = this.logs.slice(0, 60);
  }

  getLogs(): BtcEngineLog[] {
    return [...this.logs];
  }

  loadConfiguredTargets(extra: string[] = []): string[] {
    return resolveBtcAuditTargets(extra);
  }

  async fetchFeeAdvice(): Promise<BtcFeeAdvice> {
    const fees = await mempoolGet<{
      fastestFee: number;
      halfHourFee: number;
      hourFee: number;
      economyFee: number;
      minimumFee: number;
    }>("/v1/fees/recommended");
    let suggestion = "Normal Bitcoin fee market.";
    if (fees.hourFee <= 5) suggestion = "Low fee window — good for consolidating your own UTXOs.";
    else if (fees.fastestFee >= 40) suggestion = "High fees — delay non-urgent BTC consolidation.";
    else if (fees.economyFee <= fees.halfHourFee / 2) {
      suggestion = `Economy ~${fees.economyFee} sat/vB vs half-hour ${fees.halfHourFee} — wait if not urgent.`;
    }
    this.addLog("INFO", `BTC fees: fast ${fees.fastestFee} · 30m ${fees.halfHourFee} · 1h ${fees.hourFee} sat/vB`);
    return { ...fees, suggestion, sampledAt: new Date().toISOString() };
  }

  async auditAddress(address: string): Promise<BtcAddressAudit> {
    this.addLog("INFO", `BTC audit ${address.slice(0, 10)}…`);
    type AddrInfo = {
      chain_stats: { funded_txo_sum: number; spent_txo_sum: number; tx_count: number };
      mempool_stats: { funded_txo_sum: number; spent_txo_sum: number; tx_count: number };
    };
    const info = await mempoolGet<AddrInfo>(`/address/${encodeURIComponent(address)}`);
    const utxoRaw = await mempoolGet<
      { txid: string; vout: number; value: number; status: { confirmed: boolean; block_height?: number } }[]
    >(`/address/${encodeURIComponent(address)}/utxo`);

    const chainBal =
      info.chain_stats.funded_txo_sum -
      info.chain_stats.spent_txo_sum +
      (info.mempool_stats.funded_txo_sum - info.mempool_stats.spent_txo_sum);
    const utxos: BtcUtxo[] = utxoRaw.map((u) => ({
      txid: u.txid,
      vout: u.vout,
      valueSats: u.value,
      status: u.status,
    }));

    const audit: BtcAddressAudit = {
      address,
      balanceSats: chainBal,
      balanceBtc: chainBal / 1e8,
      utxoCount: utxos.length,
      chainTxCount: info.chain_stats.tx_count,
      mempoolTxCount: info.mempool_stats.tx_count,
      utxos,
      draftPayload: {
        type: "bitcoin_consolidation_intent",
        inputs: utxos.map((u) => ({ txid: u.txid, vout: u.vout, valueSats: u.valueSats })),
        note: "Unsigned intent for your BTC wallet software. Virtus does not broadcast BTC txs.",
      },
    };
    this.addLog(
      "SUCCESS",
      `${address.slice(0, 10)}… ${audit.balanceBtc} BTC · ${audit.utxoCount} UTXO · mempool txs ${audit.mempoolTxCount}`,
    );
    return audit;
  }

  async auditConfigured(extra: string[] = []): Promise<BtcAddressAudit[]> {
    const targets = this.loadConfiguredTargets(extra);
    if (targets.length === 0) {
      this.addLog("INFO", "No BTC targets (set NEXT_PUBLIC_BTC_AUDIT_TARGETS or config).");
      return [];
    }
    const out: BtcAddressAudit[] = [];
    for (const a of targets) {
      try {
        out.push(await this.auditAddress(a));
      } catch (e) {
        this.addLog("ERROR", e instanceof Error ? e.message : String(e));
      }
    }
    return out;
  }
}
