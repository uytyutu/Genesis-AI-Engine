/**
 * Corporate export helpers — CSV / JSON download from browser.
 */
import type { ChainAsset, Web3TreasuryLog } from "./secureWeb3Engine";
import type { BtcAddressAudit } from "./bitcoinEngine";
import type { GasAdvice } from "./gasOptimizer";

function downloadBlob(filename: string, mime: string, body: string) {
  const blob = new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function csvEscape(v: string | number | boolean | null | undefined): string {
  const s = String(v ?? "");
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function exportLiquidityJson(payload: {
  ethAssets: ChainAsset[];
  btcAudits: BtcAddressAudit[];
  logs: Web3TreasuryLog[];
  gas?: GasAdvice | null;
  generatedAt?: string;
}) {
  const body = JSON.stringify(
    {
      product: "Virtus Core Treasury Liquidity Audit",
      generatedAt: payload.generatedAt ?? new Date().toISOString(),
      gas: payload.gas ?? null,
      ethAssets: payload.ethAssets,
      btcAudits: payload.btcAudits,
      logs: payload.logs,
    },
    null,
    2,
  );
  downloadBlob(`virtus-treasury-audit-${Date.now()}.json`, "application/json", body);
}

export function exportLiquidityCsv(ethAssets: ChainAsset[], btcAudits: BtcAddressAudit[]) {
  const rows: string[] = [];
  rows.push(["network", "address", "balance", "symbol", "dust_or_note", "signable"].join(","));
  for (const a of ethAssets) {
    rows.push(
      [
        "ETH",
        csvEscape(a.address),
        csvEscape(a.balanceDecimal),
        csvEscape(a.symbol),
        csvEscape(a.isDust ? "DUST" : "OK"),
        csvEscape(a.canSignWithExtension ? "YES" : "READ_ONLY"),
      ].join(","),
    );
  }
  for (const b of btcAudits) {
    rows.push(
      [
        "BTC",
        csvEscape(b.address),
        csvEscape(b.balanceBtc),
        "BTC",
        csvEscape(`${b.utxoCount} utxo · ${b.mempoolTxCount} mempool`),
        "READ_ONLY",
      ].join(","),
    );
  }
  downloadBlob(`virtus-treasury-liquidity-${Date.now()}.csv`, "text/csv;charset=utf-8", rows.join("\n"));
}

export function exportLogsCsv(logs: Web3TreasuryLog[]) {
  const rows = [["timestamp", "level", "message"].join(",")];
  for (const l of logs) {
    rows.push([csvEscape(l.timestamp), csvEscape(l.level), csvEscape(l.message)].join(","));
  }
  downloadBlob(`virtus-treasury-logs-${Date.now()}.csv`, "text/csv;charset=utf-8", rows.join("\n"));
}
