export type FarmTaskEvent = {
  id: string;
  at: string;
  adapter: string;
  pay_eur: number;
  target: string;
  detail: string;
  ok: boolean;
  skipped?: boolean;
  title_ru?: string;
  lifecycle_stage?: string;
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
  payment_pending: "border-amber-500/35 bg-amber-950/15",
  payment_confirmed: "border-violet-500/35 bg-violet-950/15",
  balance_increased: "border-emerald-400/50 bg-emerald-900/25",
  task_failed: "border-rose-500/40 bg-rose-950/20",
  price_filter: "border-orange-500/35 bg-orange-950/15",
};

export function lifecycleRowClass(stage?: string): string {
  if (!stage) return "border-white/5";
  return STAGE_STYLES[stage] ?? "border-white/5";
}

export function lifecycleTitle(event: FarmTaskEvent): string {
  if (event.title_ru) return event.title_ru;
  if (event.lifecycle_stage === "balance_increased") return "Баланс увеличился";
  if (event.ok) return "Задача выполнена";
  return "Событие фермы";
}

export function showPayAmount(event: FarmTaskEvent): boolean {
  return (
    event.pay_eur > 0 &&
    (event.lifecycle_stage === "payment_confirmed" ||
      event.lifecycle_stage === "balance_increased" ||
      !event.lifecycle_stage)
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
