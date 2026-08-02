export type FarmTaskEvent = {
  id: string;
  at: string;
  adapter: string;
  pay_eur: number;
  estimate_eur?: number;
  target: string;
  detail: string;
  ok: boolean;
  skipped?: boolean;
  title_ru?: string;
  lifecycle_stage?: string;
  real_payout?: boolean;
  withdrawable?: boolean;
  payout_id?: string | null;
};

export type PayoutGuide = {
  title: string;
  steps: string[];
  threshold_usd: number;
  auto_payout: boolean;
  note: string;
};

const STAGE_STYLES: Record<string, string> = {
  task_accepted: "border-sky-500/40 bg-sky-950/20",
  task_completed: "border-emerald-500/35 bg-emerald-950/15",
  spend_accepted: "border-sky-500/35 bg-sky-950/20",
  reward_estimate: "border-zinc-500/35 bg-zinc-900/40",
  payment_pending: "border-amber-500/35 bg-amber-950/15",
  payment_confirmed: "border-violet-500/35 bg-violet-950/15",
  balance_increased: "border-emerald-400/50 bg-emerald-900/25",
  cycle_accounted: "border-zinc-500/30 bg-zinc-950/30",
  task_failed: "border-rose-500/40 bg-rose-950/20",
  price_filter: "border-orange-500/35 bg-orange-950/15",
};

export function lifecycleRowClass(stage?: string): string {
  if (!stage) return "border-white/5";
  return STAGE_STYLES[stage] ?? "border-white/5";
}

export function lifecycleTitle(event: FarmTaskEvent): string {
  if (event.title_ru) return event.title_ru;
  if (event.lifecycle_stage === "spend_accepted") {
    return "Spend OK · dataset/pipeline принят (не выплата Virtus)";
  }
  if (event.lifecycle_stage === "balance_increased") return "Баланс Earn-платформы обновился";
  if (event.lifecycle_stage === "reward_estimate") {
    return "Оценка вознаграждения (моделирование)";
  }
  if (event.lifecycle_stage === "cycle_accounted") return "Расчётный учёт цикла (не REAL)";
  if (event.lifecycle_stage === "payment_pending") {
    return "Ожидает выплаты Earn Connector (не Spend)";
  }
  if (event.ok) return "Задача обработана";
  return "Событие фермы";
}

/** Only real exchange payouts — never local estimates. */
export function showPayAmount(event: FarmTaskEvent): boolean {
  return Boolean(
    event.withdrawable ||
      event.real_payout ||
      (event.pay_eur > 0 &&
        (event.lifecycle_stage === "payment_confirmed" ||
          event.lifecycle_stage === "balance_increased")),
  );
}

export function showEstimateAmount(event: FarmTaskEvent): boolean {
  const est = Number(event.estimate_eur || 0);
  return (
    est > 0 &&
    (event.lifecycle_stage === "reward_estimate" ||
      event.lifecycle_stage === "cycle_accounted")
  );
}

export function taskTone(event: FarmTaskEvent): string {
  if (event.ok) return "text-emerald-400";
  const skipped =
    event.skipped ||
    event.detail.includes("no_key") ||
    event.detail.includes("SKIP") ||
    event.detail.includes("Toloka-only");
  return skipped ? "text-amber-300/90" : "text-rose-400";
}
