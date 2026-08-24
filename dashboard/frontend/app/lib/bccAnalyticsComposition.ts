/**
 * B3 Analytics Foundation — frontend contracts aligned with backend MetricContract.
 * Never paint fake visitors/revenue. Charts only when API returns points.
 */

export type AnalyticsConnectionState =
  | "not_connected"
  | "connected_no_data"
  | "connected_with_data"
  | "coming_soon";

export type MetricPoint = { t: string; v: number };

export type MetricContract = {
  metric_id: string;
  label: string;
  unit: string;
  period: string;
  points: MetricPoint[];
  source_id: string;
  as_of: string;
  product: string;
  point_count?: number;
};

export type AnalyticsSource = {
  source_id: string;
  label: string;
  status: AnalyticsConnectionState;
  reason: string;
  product: string;
};

export type AnalyticsPanel = {
  panel_id: string;
  product: string;
  state: AnalyticsConnectionState;
  title: string;
  metric_ids: string[];
};

export type AnalyticsOverview = {
  ok: boolean;
  engine: string;
  analytics_state: AnalyticsConnectionState;
  analytics_cta: string;
  analytics_cta_href: string;
  products: Record<
    string,
    { owned?: boolean; status?: string; order_id?: string | null }
  >;
  sources: AnalyticsSource[];
  metrics: MetricContract[];
  panels: AnalyticsPanel[];
  copy: { title?: string; body?: string; hint?: string };
};

export const BCC_ANALYTICS_EMPTY_COPY = {
  title: "Analytics noch nicht verbunden",
  body: "Verbinde Analytics, um echte Besucherdaten zu sehen.",
  law: "Keine Beispieldaten als echte Kennzahlen.",
} as const;

export function metricsForPanel(
  overview: AnalyticsOverview,
  panel: AnalyticsPanel,
): MetricContract[] {
  const ids = new Set(panel.metric_ids || []);
  return (overview.metrics || []).filter((m) => ids.has(m.metric_id));
}

export function panelStateLabel(state: AnalyticsConnectionState): string {
  if (state === "connected_with_data") return "Verbunden · Daten";
  if (state === "connected_no_data") return "Verbunden · keine Daten";
  if (state === "coming_soon") return "Coming Soon";
  return "Nicht verbunden";
}
