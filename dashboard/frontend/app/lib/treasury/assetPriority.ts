/**
 * Sort / prioritize OWN treasury assets by liquidity & fee-adjusted profitability.
 */
import type { ChainAsset } from "./secureWeb3Engine";

export interface RankedAsset extends ChainAsset {
  /** balanceWei - estimatedGasWei (wei), can be negative */
  netAfterGasWei: bigint;
  /** Higher = better to review / consolidate first */
  priorityScore: number;
  rankReason: string;
}

function toBig(v: string | number | bigint): bigint {
  return typeof v === "bigint" ? v : BigInt(v);
}

/**
 * Sort descending: signable first, then net liquidity after gas, then raw balance.
 */
export function sortAssetsByLiquidity(assets: ChainAsset[]): RankedAsset[] {
  const ranked: RankedAsset[] = assets.map((a) => {
    const bal = toBig(a.balanceWei);
    const gas = toBig(a.estimatedGasWei || "0");
    const net = bal - gas;
    const signBoost = a.canSignWithExtension ? 1e18 : 0;
    // Score in ETH-ish float for UI, plus sign boost
    const ethNet = Number(net) / 1e18;
    const priorityScore = signBoost + ethNet;
    let rankReason = "balanced";
    if (a.canSignWithExtension && net > BigInt(0)) rankReason = "signable · profitable after gas";
    else if (a.canSignWithExtension) rankReason = "signable · below gas threshold";
    else if (a.dustClass === "anomaly") rankReason = "anomaly residual";
    else if (a.isDust) rankReason = "read-only dust";
    else rankReason = "read-only · high balance";
    return { ...a, netAfterGasWei: net, priorityScore, rankReason };
  });

  ranked.sort((x, y) => {
    if (x.canSignWithExtension !== y.canSignWithExtension) {
      return x.canSignWithExtension ? -1 : 1;
    }
    if (x.netAfterGasWei !== y.netAfterGasWei) {
      return x.netAfterGasWei > y.netAfterGasWei ? -1 : 1;
    }
    return y.balanceDecimal - x.balanceDecimal;
  });

  return ranked;
}

/** Local-sim BTC UTXOs: largest net-after-single-move-fee first. */
export function sortOwnedUtxosByLiquidity(
  utxos: { id: string; amountSats: number; addressId: string; txid: string; vout: number }[],
  singleMoveFeeSats: number,
): Array<(typeof utxos)[number] & { netAfterFeeSats: number; priorityScore: number }> {
  return [...utxos]
    .map((u) => {
      const net = u.amountSats - singleMoveFeeSats;
      return { ...u, netAfterFeeSats: net, priorityScore: net };
    })
    .sort((a, b) => b.priorityScore - a.priorityScore || b.amountSats - a.amountSats);
}
