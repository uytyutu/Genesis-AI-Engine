"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { formatEur } from "./lib/formatEur";
import { LiveNarrativeFeed, type NarrativeEvent } from "./components/LiveNarrativeFeed";
import { GenesisCard } from "./components/GenesisCard";
import { AiTeamGrid } from "./components/AiTeamGrid";
import { NightShiftFeed } from "./components/NightShiftFeed";
import { NotificationRail, type NotificationItem } from "./components/NotificationRail";
import { SystemHealthBanner } from "./components/SystemHealthBanner";
import { OwnerWelcomeChecklist } from "./components/OwnerWelcomeChecklist";
import { IncomeGoalsPanel, type IncomeGoal } from "./components/IncomeGoalsPanel";
import {
  CompanyReadinessPanel,
  type CompanyReadiness,
} from "./components/CompanyReadinessPanel";
import {
  CompanyOperationsBar,
  type CompanyOperations,
} from "./components/CompanyOperationsBar";
import {
  FirstRevenueJourneyPanel,
  type FirstRevenueJourney,
} from "./components/FirstRevenueJourneyPanel";
import {
  OpportunityEnginePanel,
  type OpportunitySnapshot,
} from "./components/OpportunityEnginePanel";
import { OwnerDecisionsPanel, type MissionDecision } from "./components/OwnerDecisionsPanel";
import { SalesOrdersPanel } from "./components/SalesOrdersPanel";
import { OwnerNotificationsPanel } from "./components/OwnerNotificationsPanel";
import {
  ProductionDepartmentCard,
  type ProductionDepartment,
} from "./components/ProductionDepartmentCard";
import { CursorWorkspacePanel } from "./components/CursorWorkspacePanel";
import { DashboardSkeleton } from "./components/DashboardSkeleton";
import { Loader } from "./components/ui/Loader";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Employee = {
  id: string;
  label: string;
  icon: string;
  status: string;
  status_label: string;
  message: string;
};

type MissionControl = {
  company_name: string;
  owner_name: string;
  greeting: string;
  system_running: boolean;
  company_days: number;
  demo_mode: boolean;
  company_status_headline: string;
  revenue_today_eur: number;
  revenue_month_eur: number;
  available_for_withdrawal_eur: number;
  pending_payouts_eur: number;
  payment_connected: boolean;
  products_count: number;
  active_projects: number;
  clients: number;
  published_count: number;
  digital_employees: Employee[];
  narrative_feed: NarrativeEvent[];
  night_shift_feed: { at: string; department: string; message: string; icon: string }[];
  commercial_events: { icon: string; label: string; detail: string }[];
  recommendations_today: string[];
  morning_summary: {
    headline: string;
    owner_greeting: string;
    company_status: string;
    company_days: number;
    hours_worked: number;
    tasks_done_today: number;
    journey_progress_percent: number;
    next_goal_label: string;
    products_created_count: number;
    products_improved_count: number;
    ideas_found_count: number;
    decisions_needed_count: number;
    overnight_checklist: { icon: string; label: string; done: boolean }[];
    recommendation_title: string | null;
    recommendation_reason: string | null;
    recommendation_href: string | null;
    mode: string;
    revenue_today_eur: number;
    revenue_week_eur: number;
    payments_confirmed: number;
    pending_withdrawal_eur: number;
    company_value_eur: number;
    company_value_growth_week_percent: number;
    valuation_methodology: string;
    valuation_is_estimate: boolean;
    valuation_factors: { label: string; value_label: string; active: boolean }[];
    assets: {
      products: number;
      clients: number;
      revenue_month_eur: number;
      ai_employees: number;
      published: number;
    };
  };
  first_customer_journey?: {
    title: string;
    steps: { id: string; label: string; done: boolean }[];
    completed_count: number;
    total_count: number;
  } | null;
  first_revenue_journey?: FirstRevenueJourney | null;
  opportunity_snapshot?: OpportunitySnapshot | null;
  data_source_note: string;
  income_goals?: IncomeGoal[];
  company_readiness?: CompanyReadiness;
  company_operations?: CompanyOperations;
  production_department?: ProductionDepartment;
  decisions_needed?: MissionDecision[];
};

export default function MissionControlPage() {
  const [data, setData] = useState<MissionControl | null>(null);
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/owner/mission-control`);
      setData(await res.json());
      setMessage("");
    } catch {
      setMessage("Запустите Genesis с рабочего стола.");
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 15000);
    return () => clearInterval(t);
  }, [refresh]);

  const showJourney = data?.first_customer_journey && !data.demo_mode;
  const ms = data?.morning_summary;

  const notifications = useMemo<NotificationItem[]>(() => {
    if (!data?.narrative_feed) return [];
    return data.narrative_feed.slice(0, 6).map((e, i) => ({
      id: `n-${i}`,
      at: e.at,
      title: e.department,
      body: e.message,
      icon: e.icon,
      href: e.action_href,
    }));
  }, [data?.narrative_feed]);

  if (!data && !message) {
    return (
      <main>
        <DashboardSkeleton />
      </main>
    );
  }

  return (
    <main>
      <SystemHealthBanner />
      <CompanyOperationsBar ops={data?.company_operations} />
      <OwnerWelcomeChecklist ownerName={data?.owner_name} />
      <CompanyReadinessPanel readiness={data?.company_readiness} demoMode={data?.demo_mode} />
      {data?.first_revenue_journey && !data.demo_mode && (
        <FirstRevenueJourneyPanel journey={data.first_revenue_journey} />
      )}
      {data?.opportunity_snapshot && !data.demo_mode && (
        <OpportunityEnginePanel snapshot={data.opportunity_snapshot} />
      )}
      <IncomeGoalsPanel goals={data?.income_goals ?? []} demoMode={data?.demo_mode} />
      {data?.decisions_needed && data.decisions_needed.length > 0 && (
        <OwnerDecisionsPanel decisions={data.decisions_needed} />
      )}
      <SalesOrdersPanel />
      <OwnerNotificationsPanel />
      <div className="grid gap-5 lg:grid-cols-2">
        {data?.production_department && (
          <ProductionDepartmentCard dept={data.production_department} />
        )}
        <CursorWorkspacePanel compact />
      </div>
      <div className="flex flex-col gap-4 xl:flex-row xl:gap-6">
        <div className="min-w-0 flex-1 space-y-5">
          {ms && (
            <section className="animate-fade-up overflow-hidden rounded-3xl border border-genesis-accent/25 bg-gradient-to-br from-indigo-950/50 via-genesis-panel to-purple-950/30 p-6 shadow-glow sm:p-8">
              <p className="genesis-label text-center tracking-[0.35em] text-genesis-purple">{ms.headline}</p>

              <div className="mt-4 text-center">
                <p className="text-sm text-genesis-muted">Стоимость компании</p>
                <p className="mt-1 text-3xl font-bold tabular-nums tracking-tight sm:text-4xl">
                  ≈ {formatEur(ms.company_value_eur)}
                </p>
                {ms.company_value_growth_week_percent !== 0 && (
                  <p className={`mt-1 text-sm font-medium ${ms.company_value_growth_week_percent >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {ms.company_value_growth_week_percent >= 0 ? "↑" : "↓"}{" "}
                    {Math.abs(ms.company_value_growth_week_percent).toFixed(1)}% за неделю
                  </p>
                )}
                {ms.valuation_is_estimate && (
                  <p className="mt-2 text-[11px] text-genesis-muted">Оценка на реальных активах — не рыночная цена</p>
                )}
                <div className="mt-4 text-left">
                  <p className="genesis-label mb-2">Основано на</p>
                  <ul className="space-y-1 text-xs">
                    {ms.valuation_factors.map((f) => (
                      <li key={f.label} className="flex justify-between gap-4">
                        <span className={f.active ? "text-genesis-text" : "text-genesis-muted/70"}>
                          {f.active ? "✔" : "○"} {f.label}
                        </span>
                        <span className={`tabular-nums ${f.active ? "text-genesis-muted" : "text-genesis-muted/50"}`}>
                          {f.value_label}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="genesis-divider my-5" />

              <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
                <AssetCell icon="🏢" label="Продукты" value={ms.assets.products} />
                <AssetCell icon="👥" label="Клиенты" value={ms.assets.clients} />
                <AssetCell icon="💰" label="Доход" value={formatEur(ms.assets.revenue_month_eur)} />
                <AssetCell icon="🤖" label="AI" value={ms.assets.ai_employees} />
                <AssetCell icon="🌐" label="Опубликовано" value={ms.assets.published} />
              </div>

              <div className="genesis-divider my-5" />

              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h1 className="text-xl font-bold tracking-tight sm:text-2xl">{ms.owner_greeting}</h1>
                  <p className="mt-2 text-sm text-genesis-muted">
                    {ms.company_status}
                    {ms.hours_worked > 0 ? ` · ${ms.hours_worked} ч` : ""}
                    {ms.company_days > 0 ? ` · ${ms.company_days} дней` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2 rounded-full border border-genesis-accent/30 bg-genesis-bg/50 px-4 py-2 text-sm">
                  <span className={`h-2 w-2 rounded-full ${data?.system_running ? "status-dot-online" : "status-dot-offline"}`} />
                  {data?.company_status_headline ?? "Статус"}
                </div>
              </div>

              <div className="genesis-divider my-5" />

              {ms.mode === "revenue" ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  <StatBlock label="Доход сегодня" value={formatEur(ms.revenue_today_eur)} large />
                  <StatBlock label="За неделю" value={formatEur(ms.revenue_week_eur)} />
                  <StatBlock label="Оплат подтверждено" value={String(ms.payments_confirmed)} unit="" />
                  <StatBlock label="Ожидают вывода" value={formatEur(ms.pending_withdrawal_eur)} />
                </div>
              ) : (
                <ul className="space-y-2 text-sm">
                  {ms.overnight_checklist.map((item) => (
                    <li key={item.label} className="flex items-center gap-3">
                      <span className={item.done ? "text-emerald-400" : "text-amber-300"}>{item.icon}</span>
                      <span className={item.done ? "text-genesis-text" : "text-genesis-muted"}>{item.label}</span>
                    </li>
                  ))}
                </ul>
              )}

              {ms.recommendation_title && (
                <>
                  <div className="genesis-divider my-5" />
                  <div className="rounded-2xl border border-genesis-purple/20 bg-gradient-to-r from-genesis-accent/10 to-genesis-purple/10 p-4">
                    <p className="genesis-label text-genesis-purple">Сегодня рекомендую</p>
                    <p className="mt-2 font-semibold">{ms.recommendation_title}</p>
                    {ms.recommendation_reason && (
                      <p className="mt-2 text-sm text-genesis-muted">Причина: {ms.recommendation_reason}</p>
                    )}
                    {ms.recommendation_href && (
                      <Link
                        href={ms.recommendation_href}
                        className="mt-3 inline-block rounded-lg bg-gradient-to-r from-genesis-accent to-genesis-purple-soft px-4 py-2 text-xs font-semibold text-white hover:opacity-90"
                      >
                        Создать
                      </Link>
                    )}
                  </div>
                </>
              )}

              {showJourney && ms.mode !== "revenue" && (
                <div className="mt-5 rounded-xl border border-genesis-border-subtle bg-genesis-bg/30 p-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-genesis-muted">До первого клиента</span>
                    <span className="font-semibold">{ms.journey_progress_percent}%</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-genesis-border">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-genesis-accent to-genesis-purple transition-all duration-700"
                      style={{ width: `${ms.journey_progress_percent}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-genesis-muted">Следующая цель: {ms.next_goal_label}</p>
                </div>
              )}
            </section>
          )}

          <div className="grid gap-5 lg:grid-cols-5">
            <div className="space-y-5 lg:col-span-3">
              <GenesisCard title="🌙 Компания работала ночью" subtitle="Genesis 24/7 — даже без клиентов">
          <NightShiftFeed feed={data?.night_shift_feed ?? []} />
        </GenesisCard>

        {(data?.commercial_events?.length ?? 0) > 0 && (
          <GenesisCard title="📈 Коммерческие события">
            <ul className="space-y-3">
              {data!.commercial_events.map((e, i) => (
                <li key={`${e.label}-${i}`} className="flex items-center justify-between gap-4 text-sm">
                  <span>
                    {e.icon} {e.label}
                  </span>
                  <span className="font-semibold tabular-nums">{e.detail}</span>
                </li>
              ))}
            </ul>
          </GenesisCard>
        )}

        <GenesisCard title="💬 Genesis говорит" subtitle={data?.greeting} animate>
                {data?.narrative_feed?.length ? (
                  <LiveNarrativeFeed feed={data.narrative_feed} />
                ) : (
                  <Loader label="Genesis загружает ленту…" />
                )}
              </GenesisCard>

              <GenesisCard title="💰 Финансы">
                {showJourney ? (
                  <PaymentHubPlaceholder />
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-end justify-between gap-4">
                      <div>
                        <p className="genesis-label">Доступно</p>
                        <p className="mt-1 text-3xl font-bold tabular-nums">
                          {formatEur(data?.available_for_withdrawal_eur)}
                        </p>
                      </div>
                      <Link
                        href="/finance"
                        className="rounded-lg bg-genesis-elevated px-3 py-1.5 text-xs font-medium ring-1 ring-genesis-border hover:ring-genesis-accent/50"
                      >
                        Финансовый центр →
                      </Link>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl bg-genesis-bg/50 p-3">
                        <p className="text-genesis-muted">Сегодня</p>
                        <p className="mt-1 font-semibold text-emerald-400">{formatEur(data?.revenue_today_eur)}</p>
                      </div>
                      <div className="rounded-xl bg-genesis-bg/50 p-3">
                        <p className="text-genesis-muted">Ожидает</p>
                        <p className="mt-1 font-semibold">{formatEur(data?.pending_payouts_eur)}</p>
                      </div>
                    </div>
                  </div>
                )}
              </GenesisCard>
            </div>

            <div className="space-y-5 lg:col-span-2">
              <GenesisCard title="🤖 AI-команда" subtitle="Статус отделов в реальном времени">
                <AiTeamGrid employees={data?.digital_employees ?? []} />
              </GenesisCard>

              <GenesisCard title="🏢 Компания">
                <div className="grid grid-cols-2 gap-3">
                  <MiniMetric label="Продуктов" value={data?.products_count ?? 0} />
                  <MiniMetric label="Проектов" value={data?.active_projects ?? 0} />
                  <MiniMetric label="Клиентов" value={data?.clients ?? 0} />
                  <MiniMetric label="Опубликовано" value={data?.published_count ?? 0} />
                </div>
              </GenesisCard>
            </div>
          </div>

          {data?.demo_mode && (
            <p className="rounded-xl border border-amber-500/30 bg-amber-950/20 px-4 py-2 text-center text-xs text-amber-200/90">
              Демо-режим — цифры для оценки интерфейса, не реальные деньги
            </p>
          )}

          <GenesisCard title="💡 Рекомендации на сегодня">
            <ul className="space-y-2">
              {(data?.recommendations_today ?? []).map((r, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-genesis-accent">→</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </GenesisCard>

          <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/order"
              className="rounded-2xl bg-gradient-to-r from-genesis-accent to-indigo-600 px-8 py-3.5 text-sm font-semibold text-white shadow-glow transition hover:opacity-90"
            >
              🛒 Заказать сайт (клиент)
            </Link>
            <Link
              href="/create"
              className="rounded-2xl border border-genesis-border-subtle bg-genesis-panel/60 px-8 py-3.5 text-sm font-semibold transition hover:border-genesis-accent/40"
            >
              ➕ Создать продукт (внутри)
            </Link>
          </div>

          <p className="text-center text-xs text-genesis-muted">{data?.data_source_note}</p>
          {message && <p className="text-center text-sm text-amber-300/90">{message}</p>}
        </div>

        <NotificationRail items={notifications} />
      </div>
    </main>
  );
}

function StatBlock({
  label,
  value,
  unit,
  large,
}: {
  label: string;
  value: string;
  unit?: string;
  large?: boolean;
}) {
  return (
    <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/40 p-4">
      <p className="genesis-label">{label}</p>
      <p className={`mt-2 font-bold tabular-nums ${large ? "text-3xl" : "text-2xl"}`}>
        {value}
        {unit && <span className="ml-1 text-base font-medium text-genesis-muted">{unit}</span>}
      </p>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-genesis-bg/40 p-3 text-center">
      <p className="text-xl font-bold tabular-nums">{value}</p>
      <p className="text-[11px] text-genesis-muted">{label}</p>
    </div>
  );
}

function AssetCell({ icon, label, value }: { icon: string; label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-genesis-border-subtle bg-genesis-bg/30 p-3 text-center">
      <p className="text-lg">{icon}</p>
      <p className="mt-1 text-xs text-genesis-muted">{label}</p>
      <p className="mt-0.5 text-sm font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function PaymentHubPlaceholder() {
  const providers = [
    { icon: "🏦", label: "Банковский счёт" },
    { icon: "💳", label: "Stripe" },
    { icon: "🟦", label: "PayPal" },
    { icon: "₿", label: "Bitcoin" },
    { icon: "💵", label: "USDT" },
  ];
  return (
    <div className="space-y-4">
      <div>
        <p className="font-semibold">Payment Hub</p>
        <p className="mt-1 text-sm text-amber-300/90">Не подключён</p>
      </div>
      <p className="text-sm text-genesis-muted">
        Genesis не хранит деньги. После подключения баланс появится автоматически.
      </p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {providers.map((p) => (
          <li
            key={p.label}
            className="flex items-center gap-2 rounded-xl border border-genesis-border-subtle bg-genesis-bg/30 px-3 py-2.5 text-sm"
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
          </li>
        ))}
      </ul>
      <Link href="/finance" className="inline-block text-xs font-medium text-genesis-accent hover:underline">
        Открыть кошельки →
      </Link>
    </div>
  );
}
