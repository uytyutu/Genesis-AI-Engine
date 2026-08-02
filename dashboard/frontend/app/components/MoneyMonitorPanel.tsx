"use client";

import Link from "next/link";
import { SalesFunnelPanel } from "./SalesFunnelPanel";
import { PathAFunnelPanel } from "./PathAFunnelPanel";

export type RealMoneyTier = {
  id: string;
  icon: string;
  label_ru: string;
  amount_eur: number;
  amount_label_ru: string;
  detail_ru: string;
  payment_count?: number;
};

export type RealMoneyData = {
  rule_ru: string;
  paid_by_client?: RealMoneyTier;
  available?: RealMoneyTier;
  received: RealMoneyTier;
  pending: RealMoneyTier;
  forecast: RealMoneyTier;
  training: RealMoneyTier;
  bindings_needed?: string[];
  demo_mode?: boolean;
  payment_connected?: boolean;
};

export type SalesFunnelStep = {
  id: string;
  label_ru: string;
  count?: number | null;
  amount_eur?: number;
  amount_label_ru?: string;
  icon: string;
};

export type SalesFunnelData = {
  title_ru: string;
  headline_ru: string;
  subtitle_ru: string;
  steps: SalesFunnelStep[];
  training_note_ru?: string;
  next_action_href?: string;
};

export type MoneyMonitorLane = {
  id: string;
  icon: string;
  label_ru: string;
  amount_label_ru: string;
  status_ru: string;
  detail_ru: string;
  status?: string;
};

export type MoneyTruth = {
  real_eur: number;
  real_label_ru: string;
  spent_eur: number;
  spent_label_ru: string;
  prediction_eur: number;
  prediction_label_ru: string;
  roi_pct?: number | null;
  roi_label_ru: string;
  legend_ru?: { real?: string; spent?: string; prediction?: string };
};

export type ChannelBoardEntry = {
  id: string;
  name: string;
  mode: string;
  status: string;
  status_label_ru: string;
  note_ru?: string;
};

export type ChannelBoard = {
  title_ru?: string;
  rule_ru?: string;
  earn_channels?: ChannelBoardEntry[];
  spend_channels?: ChannelBoardEntry[];
  b2b_channels?: ChannelBoardEntry[];
  summary?: {
    earn_on_count?: number;
    verdict_ru?: string;
    performer_path_wired?: boolean;
  };
};

export type MoneyMonitorData = {
  title_ru: string;
  subtitle_ru: string;
  money_truth?: MoneyTruth | null;
  channel_board?: ChannelBoard | null;
  payout_manager?: import("./PayoutManagerPanel").PayoutManagerData | null;
  actual_revenue?: {
    paid_by_client_eur: number;
    pending_settlement_eur: number;
    available_for_withdrawal_eur: number;
    withdrawable_label_ru: string;
    paid_by_client_label_ru: string;
    pending_settlement_label_ru: string;
    source_ru: string;
    payment_count: number;
  } | null;
  farm_potential?: {
    farm_journal_eur: number;
    amount_label_ru: string;
    label_ru: string;
    detail_ru: string;
  } | null;
  real_money?: RealMoneyData | null;
  sales_funnel?: SalesFunnelData | null;
  path_a_funnel?: import("./PathAFunnelPanel").PathAFunnelData | null;
  lanes: MoneyMonitorLane[];
  withdraw_alert: {
    active: boolean;
    level: string;
    title_ru: string;
    message_ru: string;
    ceo_action_ru: string;
  };
  pipeline?: { step: number; title_ru: string; detail_ru: string }[];
  model_proven: boolean;
  model_verdict_ru: string;
  toloka_role_ru?: string;
};

type Props = {
  data: MoneyMonitorData | null | undefined;
  compact?: boolean;
};

function MoneyTruthStrip({ truth, compact }: { truth: MoneyTruth; compact?: boolean }) {
  const cells = [
    { key: "real", label: "REAL", value: truth.real_label_ru, hint: truth.legend_ru?.real, tone: "text-emerald-100 border-emerald-500/40 bg-emerald-950/30" },
    { key: "spent", label: "SPENT", value: truth.spent_label_ru, hint: truth.legend_ru?.spent, tone: "text-amber-100 border-amber-500/35 bg-amber-950/25" },
    { key: "prediction", label: "PREDICTION", value: truth.prediction_label_ru, hint: truth.legend_ru?.prediction, tone: "text-sky-100/90 border-sky-500/25 bg-sky-950/20" },
    { key: "roi", label: "ROI", value: truth.roi_label_ru, hint: "Только после REAL и SPENT", tone: "text-white/80 border-white/15 bg-genesis-bg/40" },
  ];
  return (
    <div className={`mt-4 grid gap-3 ${compact ? "grid-cols-2" : "sm:grid-cols-4"}`}>
      {cells.map((c) => (
        <div key={c.key} className={`rounded-xl border p-4 ${c.tone}`}>
          <p className="text-[10px] uppercase tracking-widest text-genesis-muted">{c.label}</p>
          <p className={`mt-2 font-bold tabular-nums ${compact ? "text-xl" : "text-2xl"}`}>{c.value}</p>
          {c.hint && !compact ? <p className="mt-2 text-[11px] leading-relaxed text-genesis-muted">{c.hint}</p> : null}
        </div>
      ))}
    </div>
  );
}

function ChannelBoardStrip({ board, compact }: { board: ChannelBoard; compact?: boolean }) {
  const earn = Array.isArray(board.earn_channels) ? board.earn_channels : [];
  const spend = Array.isArray(board.spend_channels) ? board.spend_channels : [];
  const b2b = Array.isArray(board.b2b_channels) ? board.b2b_channels : [];
  if (!earn.length && !spend.length && !b2b.length) return null;
  const renderList = (title: string, rows: ChannelBoardEntry[]) => (
    <div>
      <p className="text-[10px] uppercase tracking-widest text-genesis-muted">{title}</p>
      <ul className="mt-2 space-y-1 text-xs">
        {rows.slice(0, compact ? 3 : 6).map((r) => (
          <li key={r.id} className="flex justify-between gap-2">
            <span className="text-white/85">{r.name}</span>
            <span className={r.status === "on" ? "text-emerald-300" : "text-amber-200/80"}>
              {r.status_label_ru}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-genesis-bg/40 p-4">
      <p className="text-sm font-medium text-white">{board.title_ru ?? "Каналы"}</p>
      {board.summary?.verdict_ru ? (
        <p className="mt-1 text-xs text-amber-100/85">{board.summary.verdict_ru}</p>
      ) : null}
      <div className={`mt-3 grid gap-4 ${compact ? "grid-cols-1" : "sm:grid-cols-3"}`}>
        {renderList("Earn (платят ферме)", earn)}
        {renderList("Spend (ферма платит)", spend)}
        {renderList("B2B / Path A", b2b)}
      </div>
    </div>
  );
}

function RealMoneyHero({
  rm,
  actual,
  farm,
  truth,
  compact,
}: {
  rm: RealMoneyData;
  actual?: MoneyMonitorData["actual_revenue"];
  farm?: MoneyMonitorData["farm_potential"];
  truth?: MoneyTruth | null;
  compact?: boolean;
}) {
  const withdrawable =
    actual?.withdrawable_label_ru ?? rm.available?.amount_label_ru ?? rm.received?.amount_label_ru ?? "0,00 €";
  const paid =
    actual?.paid_by_client_label_ru ?? rm.paid_by_client?.amount_label_ru ?? "0,00 €";
  const settling =
    actual?.pending_settlement_label_ru ?? rm.pending?.amount_label_ru ?? "0,00 €";

  return (
    <div className="mt-4 space-y-4">
      {truth ? <MoneyTruthStrip truth={truth} compact={compact} /> : null}

      <div className="rounded-2xl border border-emerald-500/50 bg-gradient-to-br from-emerald-950/50 to-genesis-bg/60 p-5 sm:p-6">
        <p className="text-xs uppercase tracking-widest text-emerald-300/90">Выручка к выводу (Stripe)</p>
        <p className="mt-2 text-xs text-genesis-muted">
          {actual?.source_ru ?? rm.rule_ru}
        </p>
        <p
          className={`mt-3 font-bold tabular-nums tracking-tight text-emerald-100 ${
            compact ? "text-4xl" : "text-5xl sm:text-6xl"
          }`}
        >
          {withdrawable}
        </p>
        {!compact ? (
          <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
            <div>
              <p className="text-genesis-muted">Оплачено клиентом (REAL)</p>
              <p className="font-semibold tabular-nums text-sky-100">{paid}</p>
            </div>
            <div>
              <p className="text-genesis-muted">Settling (DE ~3 дня)</p>
              <p className="font-semibold tabular-nums text-amber-100">{settling}</p>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-xs text-genesis-muted">
            Оплачено: {paid} · Settling: {settling}
          </p>
        )}
        {actual && actual.payment_count === 0 ? (
          <p className="mt-3 rounded-lg border border-amber-500/25 bg-amber-950/20 px-3 py-2 text-xs text-amber-100/90">
            Stripe пуст — REAL = 0 € до первого webhook. PREDICTION и журнал фермы не смешиваются с выручкой.
          </p>
        ) : null}
      </div>

      <div className="rounded-xl border border-white/10 bg-genesis-bg/40 p-4">
        <p className="text-xs uppercase tracking-wide text-genesis-muted">
          {farm?.label_ru ?? rm.training?.label_ru} · estimate, не REAL
        </p>
        <p className="mt-1 text-xl font-semibold tabular-nums text-white/70">
          {farm?.amount_label_ru ?? rm.training?.amount_label_ru}
        </p>
        <p className="mt-2 text-[11px] leading-relaxed text-genesis-muted">
          {farm?.detail_ru ?? rm.training?.detail_ru}
        </p>
      </div>
    </div>
  );
}

export function MoneyMonitorPanel({ data, compact }: Props) {
  if (!data) return null;

  const alert = data.withdraw_alert;
  const lanes = Array.isArray(data.lanes) ? data.lanes : [];
  // Incomplete payload during boot must not trip Next error.tsx (500).
  if (!alert || typeof alert !== "object") return null;

  const alertBorder =
    alert.level === "green"
      ? "border-emerald-400/50 bg-emerald-950/30"
      : alert.level === "amber"
        ? "border-amber-400/40 bg-amber-950/25"
        : "border-white/10 bg-genesis-bg/30";

  return (
    <section className={`rounded-2xl border p-5 ${alertBorder}`}>
      {data.sales_funnel && compact ? (
        <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-4">
          <p className="text-xs uppercase tracking-wider text-violet-200/80">Mission 2</p>
          <p className="mt-1 text-lg font-semibold text-white">{data.sales_funnel.headline_ru}</p>
          <p className="mt-1 text-xs text-genesis-muted">{data.sales_funnel.subtitle_ru}</p>
          <Link
            href={data.sales_funnel.next_action_href ?? "/business"}
            className="mt-3 inline-flex text-sm text-emerald-400 hover:underline"
          >
            Открыть Business Health →
          </Link>
        </div>
      ) : null}

      {!compact && data.sales_funnel ? <SalesFunnelPanel data={data.sales_funnel} compact={compact} /> : null}
      {!compact && data.path_a_funnel ? (
        <div className="mt-4">
          <PathAFunnelPanel data={data.path_a_funnel} compact={compact} />
        </div>
      ) : null}

      <div className={`${(data.sales_funnel || data.path_a_funnel) && !compact ? "mt-4" : compact && data.sales_funnel ? "mt-4" : ""} flex flex-wrap items-start justify-between gap-3`}>
        <div>
          <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
          <p className="mt-1 text-sm text-genesis-muted">{data.subtitle_ru}</p>
          <p className={`mt-2 text-sm font-medium ${data.model_proven ? "text-emerald-300" : "text-amber-200"}`}>
            {data.model_verdict_ru}
          </p>
        </div>
        {!compact ? (
          <Link href="/business" className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-sm text-emerald-200 hover:bg-emerald-950/30">
            CEO Outbox →
          </Link>
        ) : null}
      </div>

      {data.real_money ? (
        <RealMoneyHero
          rm={data.real_money}
          actual={data.actual_revenue}
          farm={data.farm_potential}
          truth={data.money_truth}
          compact={compact}
        />
      ) : data.money_truth ? (
        <MoneyTruthStrip truth={data.money_truth} compact={compact} />
      ) : null}

      {data.channel_board && !compact ? (
        <ChannelBoardStrip board={data.channel_board} compact={compact} />
      ) : null}

      <div className={`mt-4 grid gap-3 ${compact ? "sm:grid-cols-1" : "sm:grid-cols-3"}`}>
        {lanes.map((lane) => (
          <div
            key={lane.id}
            className={`rounded-xl border p-4 ${
              lane.id === "b2b_client"
                ? "border-emerald-500/35 bg-emerald-950/20"
                : lane.id === "exchange_factory"
                  ? "border-sky-500/25 bg-sky-950/15"
                  : "border-white/10 bg-genesis-bg/40"
            }`}
          >
            <p className="text-lg">{lane.icon}</p>
            <p className="mt-1 text-xs uppercase tracking-wide text-genesis-muted">{lane.label_ru}</p>
            <p className="mt-2 text-lg font-semibold tabular-nums">{lane.amount_label_ru}</p>
            <p className="mt-1 text-xs text-emerald-200/80">{lane.status_ru}</p>
            <p className="mt-2 text-[11px] leading-relaxed text-genesis-muted">{lane.detail_ru}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 rounded-xl border border-white/10 bg-genesis-bg/40 p-4">
        <p className="font-medium text-white">{alert.title_ru}</p>
        <p className="mt-1 text-sm text-genesis-muted">{alert.message_ru}</p>
        <p className="mt-2 text-xs text-emerald-200/90">→ {alert.ceo_action_ru}</p>
        <Link
          href="/payout"
          className="mt-3 inline-flex text-sm font-medium text-emerald-300 hover:underline"
        >
          Открыть Вывод · Payout Manager →
        </Link>
      </div>

      {data.toloka_role_ru && !compact ? (
        <p className="mt-3 text-xs text-sky-200/70">{data.toloka_role_ru}</p>
      ) : null}

      {data.pipeline && data.pipeline.length > 0 && !compact ? (
        <ol className="mt-4 space-y-1 text-xs text-genesis-muted">
          {data.pipeline.map((p) => (
            <li key={p.step}>
              <span className="text-white/80">{p.step}. {p.title_ru}</span> — {p.detail_ru}
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
