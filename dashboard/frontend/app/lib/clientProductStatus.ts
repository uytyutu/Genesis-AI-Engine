/** Honest client product status — no decorative Active/Live fallbacks. */

export type HonestProductStatus =
  | "active"
  | "pending"
  | "not_activated"
  | "coming_soon"
  | "unknown";

export type HonestStatusDisplay = {
  key: HonestProductStatus;
  label: string;
  toneClass: string;
};

const LABEL: Record<HonestProductStatus, string> = {
  active: "Active",
  pending: "Pending",
  not_activated: "Not activated",
  coming_soon: "Coming Soon",
  unknown: "Unknown",
};

const TONE: Record<HonestProductStatus, string> = {
  active: "text-emerald-300",
  pending: "text-amber-300",
  not_activated: "text-zinc-500",
  coming_soon: "text-violet-300/90",
  unknown: "text-zinc-500",
};

function display(key: HonestProductStatus): HonestStatusDisplay {
  return { key, label: LABEL[key], toneClass: TONE[key] };
}

function norm(raw: string | undefined | null): string {
  return String(raw || "")
    .trim()
    .toLowerCase();
}

const ACTIVE = [
  "ready",
  "completed",
  "delivered",
  "active",
  "done",
  "live",
  "published",
  "bereit",
  "fertig",
  "aktiv",
];

const PENDING = [
  "pending",
  "processing",
  "progress",
  "in progress",
  "laufend",
  "in bearbeitung",
  "queued",
  "building",
  "working",
  "preparing",
];

const COMING = ["coming", "soon", "planned", "gen2"];

const INACTIVE = [
  "not activated",
  "inactive",
  "nicht aktiviert",
  "not_activated",
  "none",
  "disabled",
];

function classify(raw: string): HonestProductStatus | null {
  const st = norm(raw);
  if (!st) return null;
  if (ACTIVE.some((x) => st.includes(x))) return "active";
  if (PENDING.some((x) => st.includes(x))) return "pending";
  if (COMING.some((x) => st.includes(x))) return "coming_soon";
  if (INACTIVE.some((x) => st.includes(x))) return "not_activated";
  return null;
}

export type OrderStatusInput = {
  status?: string | null;
  status_label?: string | null;
  download_ready?: boolean;
  shop_pipeline_label?: string | null;
};

export function resolveOrderHonestStatus(
  order: OrderStatusInput | null | undefined,
): HonestStatusDisplay {
  if (!order) return display("unknown");

  if (order.download_ready) return display("active");

  const candidates = [
    order.status_label,
    order.shop_pipeline_label,
    order.status,
  ];
  for (const raw of candidates) {
    const hit = classify(String(raw || ""));
    if (hit) return display(hit);
  }

  if (candidates.some((c) => String(c || "").trim())) {
    return display("unknown");
  }

  return display("unknown");
}

export type PortalProductStatusInput = {
  status?: string;
};

export function resolvePortalProductHonestStatus(
  product: PortalProductStatusInput | null | undefined,
): HonestStatusDisplay {
  if (!product) return display("unknown");
  const hit = classify(product.status || "");
  if (hit) return display(hit);
  if (String(product.status || "").trim()) return display("unknown");
  return display("unknown");
}
