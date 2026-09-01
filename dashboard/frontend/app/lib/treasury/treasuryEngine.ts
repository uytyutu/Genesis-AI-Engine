/**
 * Treasury Routing — batch consolidate OWN UTXOs to owner's vault address.
 * Never invents third-party sources. Broadcast stays local/simulation until wallet adapter.
 */
import { assessDust, estimateConsolidationFee, filterOwnedUtxos } from "./portfolioOptimizer";
import type {
  ConsolidationPlan,
  OwnedAddress,
  OwnedUtxo,
  TreasuryLog,
  TreasuryStorageSnapshot,
} from "./types";
import { TREASURY_STORAGE_KEY } from "./types";

export type { OwnedAddress, OwnedUtxo, ConsolidationPlan, TreasuryLog, TreasuryStorageSnapshot };

function uid(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function nowLog(level: TreasuryLog["level"], message: string): TreasuryLog {
  return {
    id: uid("log"),
    level,
    message,
    at: new Date().toLocaleTimeString(),
  };
}

export class TreasuryEngine {
  private static instance: TreasuryEngine | null = null;
  private addresses: OwnedAddress[] = [];
  private utxos: OwnedUtxo[] = [];
  private plans: ConsolidationPlan[] = [];
  private vaultAddress = "";
  private logs: TreasuryLog[] = [];

  private constructor() {
    this.hydrate();
    this.pushLog("INFO", "Treasury Engine ready — OWN wallets only.");
  }

  static getInstance(): TreasuryEngine {
    if (!TreasuryEngine.instance) TreasuryEngine.instance = new TreasuryEngine();
    return TreasuryEngine.instance;
  }

  private hydrate() {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(TREASURY_STORAGE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw) as TreasuryStorageSnapshot;
      this.addresses = data.addresses ?? [];
      this.utxos = data.utxos ?? [];
      this.plans = data.plans ?? [];
      this.vaultAddress = data.vaultAddress ?? "";
      this.logs = data.logs ?? [];
    } catch {
      this.pushLog("WARNING", "Could not restore treasury snapshot.");
    }
  }

  private persist() {
    if (typeof window === "undefined") return;
    const snap: TreasuryStorageSnapshot = {
      addresses: this.addresses,
      utxos: this.utxos,
      plans: this.plans,
      vaultAddress: this.vaultAddress,
      logs: this.logs.slice(0, 80),
    };
    localStorage.setItem(TREASURY_STORAGE_KEY, JSON.stringify(snap));
  }

  private pushLog(level: TreasuryLog["level"], message: string) {
    this.logs.unshift(nowLog(level, message));
    this.logs = this.logs.slice(0, 80);
    this.persist();
  }

  getSnapshot(): TreasuryStorageSnapshot {
    return {
      addresses: [...this.addresses],
      utxos: [...this.utxos],
      plans: [...this.plans],
      vaultAddress: this.vaultAddress,
      logs: [...this.logs],
    };
  }

  setVaultAddress(address: string) {
    this.vaultAddress = address.trim();
    this.pushLog("INFO", `Vault address set (${this.vaultAddress.slice(0, 12)}…).`);
    this.persist();
  }

  /**
   * Register an address you control. Routing refuses ownershipConfirmed=false.
   */
  registerOwnedAddress(input: {
    label: string;
    address: string;
    kind: OwnedAddress["kind"];
    ownershipConfirmed: boolean;
  }): OwnedAddress {
    if (!input.ownershipConfirmed) {
      throw new Error("Ownership must be confirmed before registering for treasury routing.");
    }
    const addr: OwnedAddress = {
      id: uid("addr"),
      label: input.label.trim() || "Owned wallet",
      address: input.address.trim(),
      kind: input.kind,
      ownershipConfirmed: true,
      addedAt: Date.now(),
    };
    this.addresses.push(addr);
    this.pushLog("SUCCESS", `Registered owned address: ${addr.label}`);
    this.persist();
    return addr;
  }

  /** Manual UTXO import for addresses you already own (wallet export / descriptor). */
  importOwnedUtxo(input: Omit<OwnedUtxo, "id">): OwnedUtxo {
    const parent = this.addresses.find((a) => a.id === input.addressId && a.ownershipConfirmed);
    if (!parent) throw new Error("UTXO parent address is not ownership-confirmed.");
    const u: OwnedUtxo = { ...input, id: uid("utxo") };
    this.utxos.push(u);
    this.pushLog("INFO", `Imported owned UTXO ${u.amountSats} sats @ ${parent.label}`);
    this.persist();
    return u;
  }

  /** Demo seed — still tagged as owner-attested sample data, not chain discovery. */
  seedDemoOwnedPortfolio() {
    if (this.addresses.length > 0) {
      this.pushLog("WARNING", "Demo seed skipped — portfolio already has addresses.");
      return;
    }
    const a1 = this.registerOwnedAddress({
      label: "CEO Hot Wallet",
      address: "bc1q_example_owner_hot_do_not_use_on_mainnet",
      kind: "hot",
      ownershipConfirmed: true,
    });
    const a2 = this.registerOwnedAddress({
      label: "CEO Cold Vault Source",
      address: "bc1q_example_owner_cold_do_not_use_on_mainnet",
      kind: "cold",
      ownershipConfirmed: true,
    });
    this.setVaultAddress("bc1q_example_owner_vault_do_not_use_on_mainnet");
    const samples: Omit<OwnedUtxo, "id">[] = [
      { addressId: a1.id, txid: "demo_tx_a", vout: 0, amountSats: 125_000, confirmations: 12, scriptType: "p2wpkh" },
      { addressId: a1.id, txid: "demo_tx_b", vout: 1, amountSats: 420, confirmations: 40, scriptType: "p2wpkh" },
      { addressId: a1.id, txid: "demo_tx_c", vout: 2, amountSats: 890, confirmations: 8, scriptType: "p2wpkh" },
      { addressId: a2.id, txid: "demo_tx_d", vout: 0, amountSats: 50_000, confirmations: 100, scriptType: "p2tr" },
      { addressId: a2.id, txid: "demo_tx_e", vout: 3, amountSats: 300, confirmations: 200, scriptType: "p2wpkh" },
    ];
    for (const s of samples) this.importOwnedUtxo(s);
    this.pushLog("INFO", "Loaded DEMO owned UTXOs (placeholders — replace with your wallet export).");
  }

  buildConsolidationPlan(satPerVbyte = 12): ConsolidationPlan {
    if (!this.vaultAddress) throw new Error("Set your verified vault address first.");
    const owned = filterOwnedUtxos(this.addresses, this.utxos);
    if (owned.length === 0) throw new Error("No ownership-confirmed UTXOs to consolidate.");

    const dust = assessDust(owned, satPerVbyte);
    const batchIds = new Set(dust.filter((d) => d.includeInBatch).map((d) => d.utxoId));
    let inputs = owned.filter((u) => batchIds.has(u.id));
    if (inputs.length < 2) {
      // Fall back to all owned UTXOs if too few dust tails
      inputs = owned;
    }
    const fee = estimateConsolidationFee(inputs.length, 1, satPerVbyte);
    const totalIn = inputs.reduce((s, u) => s + u.amountSats, 0);
    const net = totalIn - fee.estimatedFeeSats;
    if (net <= 0) throw new Error("Consolidation not profitable at current fee estimate.");

    const plan: ConsolidationPlan = {
      planId: uid("plan"),
      sourceAddressIds: [...new Set(inputs.map((u) => u.addressId))],
      destinationAddress: this.vaultAddress,
      inputUtxoIds: inputs.map((u) => u.id),
      totalInputSats: totalIn,
      estimatedFeeSats: fee.estimatedFeeSats,
      netOutputSats: net,
      status: "AWAITING_OK",
      createdAt: Date.now(),
      broadcastMode: "simulation_local",
      lastMessage: "Plan ready. Confirm via OK Protocol before local sign.",
    };
    this.plans.unshift(plan);
    this.pushLog(
      "SUCCESS",
      `Draft plan ${plan.planId}: ${inputs.length} own UTXOs → vault, net ${net} sats (est. fee ${fee.estimatedFeeSats}).`,
    );
    this.persist();
    return plan;
  }

  /** Step 1 of OK protocol — human confirmation only. */
  confirmOk(planId: string, okPhrase: string): ConsolidationPlan {
    const plan = this.plans.find((p) => p.planId === planId);
    if (!plan) throw new Error("Plan not found.");
    if (plan.status !== "AWAITING_OK" && plan.status !== "DRAFT") {
      throw new Error(`Plan status ${plan.status} cannot accept OK.`);
    }
    if (okPhrase.trim() !== "OK") {
      plan.status = "REJECTED";
      plan.lastMessage = "OK phrase rejected.";
      this.pushLog("WARNING", `OK rejected for ${planId}.`);
      this.persist();
      return plan;
    }
    plan.status = "OK_CONFIRMED";
    plan.okConfirmedAt = Date.now();
    plan.lastMessage = "OK confirmed. Ready for local wallet sign (adapter stub).";
    this.pushLog("SUCCESS", `OK Protocol confirmed for ${planId}.`);
    this.persist();
    return plan;
  }

  /**
   * Local sign stub — does NOT touch third-party keys or broadcast mainnet.
   * Marks SETTLED_LOCAL only in simulation mode for CEO UX rehearsal.
   */
  signLocalSimulation(planId: string): ConsolidationPlan {
    const plan = this.plans.find((p) => p.planId === planId);
    if (!plan) throw new Error("Plan not found.");
    if (plan.status !== "OK_CONFIRMED" && plan.status !== "AWAITING_LOCAL_SIGN") {
      throw new Error("OK confirmation required before local sign.");
    }
    plan.status = "SETTLED_LOCAL";
    plan.lastMessage =
      "LOCAL SIMULATION settled. Wire a real wallet adapter for mainnet broadcast of YOUR keys only.";
    this.pushLog("SUCCESS", `Local simulation complete for ${planId} (not on-chain).`);
    this.persist();
    return plan;
  }
}
