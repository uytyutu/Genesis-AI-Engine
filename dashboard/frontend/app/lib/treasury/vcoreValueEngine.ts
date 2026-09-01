/**
 * Value Engine layers — never collapse into one fake number.
 * DECLARED / MODEL ≠ MARKET ≠ EXECUTABLE ≠ REAL SETTLEMENT
 */

export type ValueLayerId =
  | "declared"
  | "model"
  | "market"
  | "executable"
  | "realSettlement";

export interface ValueLayer {
  label: string;
  amount: number;
  unit: string;
  note: string;
  model?: string;
  tx?: string | null;
}

export interface ValueEngineSnapshot {
  declared: ValueLayer;
  model: ValueLayer;
  market: ValueLayer;
  executable: ValueLayer;
  realSettlement: ValueLayer;
  hypothesis:
    | "MODEL_ONLY"
    | "EXECUTABLE_PARTIAL"
    | "REAL_SETTLED"
    | "EMPTY";
}

export function classifyHypothesis(v: ValueEngineSnapshot): ValueEngineSnapshot["hypothesis"] {
  if (v.realSettlement.amount > 0) return "REAL_SETTLED";
  if (v.executable.amount > 0) return "EXECUTABLE_PARTIAL";
  if (v.model.amount > 0 || v.declared.amount > 0) return "MODEL_ONLY";
  return "EMPTY";
}

export function emptyValueEngine(supplyHuman = 1_000_000): ValueEngineSnapshot {
  const ref = Number(supplyHuman);
  const snap: ValueEngineSnapshot = {
    declared: {
      label: "DECLARED VALUE",
      amount: ref,
      unit: "USD",
      note: "Reference 1 VCORE = $1 — not money.",
    },
    model: {
      label: "MODEL VALUE",
      amount: ref,
      unit: "USD",
      model: "A_FIXED_EMISSION",
      note: "Model A fixed emission. Not market.",
    },
    market: {
      label: "MARKET VALUE",
      amount: 0,
      unit: "USD",
      note: "No pool / no listing.",
    },
    executable: {
      label: "EXECUTABLE VALUE",
      amount: 0,
      unit: "TON",
      note: "Conversion quote. 0 until liquidity.",
    },
    realSettlement: {
      label: "REALIZED VALUE",
      amount: 0,
      unit: "TON",
      tx: null,
      note: "Only after confirmed swap/payout on chain. Alias: REAL SETTLEMENT.",
    },
    hypothesis: "MODEL_ONLY",
  };
  snap.hypothesis = classifyHypothesis(snap);
  return snap;
}
