"use client";

export type PathAFunnelTop = { id: string; count: number };

export type PathAFunnelData = {
  title_ru: string;
  headline_ru: string;
  subtitle_ru: string;
  steps: {
    id: string;
    label_ru: string;
    count?: number | null;
    icon: string;
  }[];
  conversion_view_to_paid_pct?: number;
  top_niches?: PathAFunnelTop[];
  top_products?: PathAFunnelTop[];
  top_specializations?: PathAFunnelTop[];
  next_action_href?: string;
  /** A2.1 — nested Order Experience / Checkout funnel (same card shape). */
  order_experience_funnel?: PathAFunnelData | null;
};

type Props = {
  data: PathAFunnelData | null | undefined;
  compact?: boolean;
};

function FunnelCard({ data, compact }: { data: PathAFunnelData; compact?: boolean }) {
  const many = (data.steps?.length ?? 0) > 6;
  return (
    <section className="rounded-2xl border border-sky-500/35 bg-gradient-to-br from-sky-950/35 to-genesis-bg/50 p-5">
      <div>
        <h2 className="text-lg font-semibold text-white">{data.title_ru}</h2>
        <p className="mt-1 text-sm font-medium text-sky-200/90">{data.headline_ru}</p>
        <p className="mt-1 text-xs text-genesis-muted">{data.subtitle_ru}</p>
        {data.conversion_view_to_paid_pct != null ? (
          <p className="mt-2 text-xs text-sky-100/80">
            {data.title_ru.includes("Order Experience") ? "Start → Paid" : "View → Paid"}:{" "}
            {data.conversion_view_to_paid_pct}%
          </p>
        ) : null}
      </div>

      <div
        className={`mt-4 grid gap-2 ${
          compact || many
            ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-5"
            : "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6"
        }`}
      >
        {(data.steps ?? []).map((step) => (
          <div
            key={step.id}
            className="rounded-xl border border-white/10 bg-genesis-bg/40 p-3"
          >
            <p className="text-xs text-genesis-muted">
              {step.icon} {step.label_ru}
            </p>
            <p
              className={`mt-1 font-bold tabular-nums text-white ${
                compact || many ? "text-xl" : "text-2xl"
              }`}
            >
              {step.count ?? 0}
            </p>
          </div>
        ))}
      </div>

      {!compact && (data.top_niches?.length || data.top_products?.length) ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 text-xs text-genesis-muted">
          {data.top_niches && data.top_niches.length > 0 ? (
            <div>
              <p className="font-medium text-sky-100/90">Топ ниши</p>
              <ul className="mt-1 space-y-0.5">
                {data.top_niches.slice(0, 5).map((n) => (
                  <li key={n.id}>
                    {n.id}: {n.count}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {data.top_products && data.top_products.length > 0 ? (
            <div>
              <p className="font-medium text-sky-100/90">Топ Visual Experience</p>
              <ul className="mt-1 space-y-0.5">
                {data.top_products.slice(0, 5).map((n) => (
                  <li key={n.id}>
                    {n.id}: {n.count}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

export function PathAFunnelPanel({ data, compact }: Props) {
  if (!data) return null;
  const oe = data.order_experience_funnel;
  const pathAOnly = { ...data, order_experience_funnel: undefined };

  return (
    <div className="space-y-4">
      {oe ? <FunnelCard data={oe} compact={compact} /> : null}
      <FunnelCard data={pathAOnly} compact={compact} />
    </div>
  );
}
