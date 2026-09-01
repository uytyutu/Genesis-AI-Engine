/**
 * Portfolio Discovery — audit OWN registered addresses + UTXO tails only.
 */
import type { DustAssessment, FeeEstimate, OwnedAddress, OwnedUtxo } from "./types";

/** Default dust heuristic (satoshis). Below this → candidate for batch only. */
export const DUST_THRESHOLD_SATS = 546;

/** Conservative fee rate for planning (not a live oracle). */
export const DEFAULT_SAT_PER_VBYTE = 12;

export function estimateConsolidationFee(
  inputCount: number,
  outputCount = 1,
  satPerVbyte = DEFAULT_SAT_PER_VBYTE,
): FeeEstimate {
  // Rough P2WPKH sizing: ~68 vB/in + 31 vB/out + 10 overhead
  const estimatedVbytes = Math.max(110, inputCount * 68 + outputCount * 31 + 10);
  const estimatedFeeSats = estimatedVbytes * satPerVbyte;
  return {
    satPerVbyte,
    estimatedVbytes,
    estimatedFeeSats,
    networkHint: "Planning estimate only — refresh from your wallet/node before broadcast.",
  };
}

export function assessDust(
  utxos: OwnedUtxo[],
  satPerVbyte = DEFAULT_SAT_PER_VBYTE,
): DustAssessment[] {
  const singleMoveFee = estimateConsolidationFee(1, 1, satPerVbyte).estimatedFeeSats;
  return utxos.map((u) => {
    const isUneconomicAlone = u.amountSats <= singleMoveFee || u.amountSats <= DUST_THRESHOLD_SATS;
    const includeInBatch = u.amountSats > 0 && (isUneconomicAlone || u.amountSats < singleMoveFee * 3);
    return {
      utxoId: u.id,
      amountSats: u.amountSats,
      estimatedFeeSats: singleMoveFee,
      isUneconomicAlone,
      includeInBatch,
      note: isUneconomicAlone
        ? "Uneconomic alone — include only in batch consolidation of your own UTXOs."
        : "Spendable alone; batch still reduces average fee.",
    };
  });
}

export function portfolioTotals(utxos: OwnedUtxo[]) {
  const totalSats = utxos.reduce((s, u) => s + u.amountSats, 0);
  const dust = assessDust(utxos);
  const dustSats = dust.filter((d) => d.isUneconomicAlone).reduce((s, d) => s + d.amountSats, 0);
  const batchCandidates = dust.filter((d) => d.includeInBatch);
  return {
    totalSats,
    dustSats,
    utxoCount: utxos.length,
    dustCount: dust.filter((d) => d.isUneconomicAlone).length,
    batchCandidateCount: batchCandidates.length,
    assessments: dust,
  };
}

/** Keep only UTXOs whose addressId belongs to ownership-confirmed addresses. */
export function filterOwnedUtxos(addresses: OwnedAddress[], utxos: OwnedUtxo[]): OwnedUtxo[] {
  const ok = new Set(addresses.filter((a) => a.ownershipConfirmed).map((a) => a.id));
  return utxos.filter((u) => ok.has(u.addressId));
}

export class PortfolioOptimizer {
  assess(addresses: OwnedAddress[], utxos: OwnedUtxo[], satPerVbyte = DEFAULT_SAT_PER_VBYTE) {
    const owned = filterOwnedUtxos(addresses, utxos);
    const totals = portfolioTotals(owned);
    const batchFee = estimateConsolidationFee(
      Math.max(1, totals.batchCandidateCount),
      1,
      satPerVbyte,
    );
    return {
      ownedAddressCount: addresses.filter((a) => a.ownershipConfirmed).length,
      ...totals,
      batchFee,
      profitable:
        totals.dustSats > batchFee.estimatedFeeSats && totals.batchCandidateCount >= 2,
    };
  }
}
