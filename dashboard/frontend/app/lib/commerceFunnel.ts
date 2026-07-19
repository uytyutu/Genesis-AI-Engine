import { getVisitorId } from "./visitorId";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export type FunnelEvent =
  | "tier_page_view"
  | "tier_select"
  | "premium_preview_view"
  | "upgrade_click"
  | "checkout_start"
  | "checkout_paid"
  | "specialization_selected"
  | "vxp_product_shown";

export type FunnelMeta = {
  niche?: string | null;
  niche_id?: string | null;
  specialization?: string | null;
  specialization_id?: string | null;
  product_id?: string | null;
  order_id?: string | null;
  mode?: string | null;
  visitor_id?: string | null;
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
