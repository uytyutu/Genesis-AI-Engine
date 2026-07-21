import { getVisitorId } from "./visitorId";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

/** Path A + Order Experience v2 funnel events (pricing_analytics.jsonl). */
export type FunnelEvent =
  | "tier_page_view"
  | "tier_select"
  | "premium_preview_view"
  | "upgrade_click"
  | "checkout_start"
  | "checkout_paid"
  | "specialization_selected"
  | "vxp_product_shown"
  // A2.1 — Order Experience funnel
  | "order_started"
  | "step_1_completed"
  | "step_2_completed"
  | "step_3_completed"
  | "step_4_completed"
  | "draft_restored"
  | "checkout_summary_viewed"
  | "checkout_confirmed"
  | "stripe_redirect_started"
  | "stripe_return_success"
  | "stripe_return_cancel"
  | "order_completed";

export type FunnelMeta = {
  niche?: string | null;
  niche_id?: string | null;
  specialization?: string | null;
  specialization_id?: string | null;
  product_id?: string | null;
  order_id?: string | null;
  mode?: string | null;
  visitor_id?: string | null;
  form_step?: number | null;
  market_code?: string | null;
  [key: string]: unknown;
};

/** Path A commerce funnel — fire-and-forget into pricing-event jsonl. */
export function logCommerceEvent(
  event: FunnelEvent,
  tierId: string | null,
  page: string,
  meta: FunnelMeta = {},
): void {
  let visitor_id = meta.visitor_id;
  if (!visitor_id && typeof window !== "undefined") {
    try {
      visitor_id = getVisitorId("public");
    } catch {
      visitor_id = null;
    }
  }
  const payload = {
    event,
    tier_id: tierId,
    page,
    meta: {
      ...meta,
      visitor_id: visitor_id || undefined,
    },
  };
  fetch(`${API}/api/public/pricing-event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).catch(() => undefined);
}
