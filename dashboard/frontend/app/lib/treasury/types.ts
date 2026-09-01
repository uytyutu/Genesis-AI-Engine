/**
 * Virtus Core — Portfolio & Treasury Optimizer (OWN WALLETS ONLY)
 *
 * Scope lock:
 * - Operates only on addresses the owner explicitly registers.
 * - Does NOT scan public chain for third-party / dormant / unclaimed funds.
 * - Does NOT invent REAL ledger income (Finance Reality Law).
 * - Broadcast requires a future wallet adapter; default = local draft + OK confirm.
 */

export type OwnedAddressKind = "hot" | "cold" | "liquidity_pool" | "exchange_deposit";

export interface OwnedAddress {
  id: string;
  label: string;
  address: string;
  kind: OwnedAddressKind;
  /** Owner attestation — required before any routing */
  ownershipConfirmed: boolean;
  addedAt: number;
}

export interface OwnedUtxo {
  id: string;
  addressId: string;
  txid: string;
  vout: number;
  /** Value in satoshis (BTC) or smallest units for the asset */
  amountSats: number;
  confirmations: number;
  scriptType: "p2wpkh" | "p2tr" | "p2sh" | "other";
}

export interface DustAssessment {
  utxoId: string;
  amountSats: number;
  estimatedFeeSats: number;
  /** true if fee to move alone would exceed value (uneconomic dust) */
  isUneconomicAlone: boolean;
  /** true if worth including in a batch consolidation */
  includeInBatch: boolean;
  note: string;
}

export interface FeeEstimate {
  satPerVbyte: number;
  estimatedVbytes: number;
  estimatedFeeSats: number;
  networkHint: string;
}

export type ConsolidationStatus =
  | "DRAFT"
  | "AWAITING_OK"
  | "OK_CONFIRMED"
  | "AWAITING_LOCAL_SIGN"
  | "SIGNED_LOCAL"
  | "BROADCAST_PENDING"
  | "SETTLED_LOCAL"
  | "REJECTED"
  | "FAILED";

export interface ConsolidationPlan {
  planId: string;
  sourceAddressIds: string[];
  destinationAddress: string;
  inputUtxoIds: string[];
  totalInputSats: number;
  estimatedFeeSats: number;
  netOutputSats: number;
  status: ConsolidationStatus;
  createdAt: number;
  okConfirmedAt?: number;
  /** Honest: no chain tx until a real wallet adapter is wired */
  broadcastMode: "simulation_local" | "wallet_adapter";
  lastMessage: string;
}

export interface TreasuryLog {
  id: string;
  level: "INFO" | "SUCCESS" | "WARNING" | "ERROR";
  message: string;
  at: string;
}

export interface TreasuryStorageSnapshot {
  addresses: OwnedAddress[];
  utxos: OwnedUtxo[];
  plans: ConsolidationPlan[];
  vaultAddress: string;
  logs: TreasuryLog[];
}

export const TREASURY_STORAGE_KEY = "virtus_core_treasury_v1";
