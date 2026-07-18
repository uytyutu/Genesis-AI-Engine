import { PRICING_FALLBACK } from "./pricingFallback";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export type PricingTier = {
  id: string;
  name: string;
  price_eur_month: number | null;
  price_label: string;
  period: string;
  audience: string;
  tagline?: string;
  features: string[];
  cta: string;
  cta_href: string;
  highlight?: boolean;
  available?: boolean;
  contact_only?: boolean;
};

export type PricingService = {
  id: string;
  name: string;
  price_label: string;
  description: string;
  cta: string;
  cta_href: string;
  available?: boolean;
};

export type ServiceCatalogItem = {
  id: string;
  name: string;
  price_label: string;
  timeline?: string;
  includes?: string[];
  description: string;
  cta: string;
  cta_href: string;
  available?: boolean;
  tier?: string;
};

export type ServiceCategory = {
  id: string;
  name: string;
  description: string;
  items: ServiceCatalogItem[];
};

export type CapabilityGroup = {
  title: string;
  items: string[];
};

export type ComparisonColumn = { id: string; label: string };
export type ComparisonRow = { feature: string; values: string[] };

export type BusinessUnit = {
  id: string;
  name: string;
  tagline: string;
  includes: string[];
  cta: string;
  cta_href: string;
};

export type PricingDisplay = {
  version: string;
  disclaimer?: { ru?: string; de?: string };
  platform_status?: Record<string, string>;
  capabilities?: {
    headline: string;
    subheadline: string;
    groups: CapabilityGroup[];
    value_anchor: string;
  };
  service_vs_product?: {
    headline: string;
    service_when: string;
    product_when: string;
    cta_service: { label: string; href: string };
    cta_product: { label: string; href: string };
  };
  anti_cannibalization?: {
    headline: string;
    body: string;
    example_one_site: string;
  };
  service_categories?: ServiceCategory[];
  comparison?: { columns: ComparisonColumn[]; rows: ComparisonRow[] };
  subscriptions: PricingTier[];
  services: PricingService[];
  business_units: BusinessUnit[];
};

export async function fetchPricingDisplay(): Promise<PricingDisplay> {
  try {
    const res = await fetch(`${API}/api/public/pricing`, { cache: "no-store" });
    if (!res.ok) return PRICING_FALLBACK;
    return (await res.json()) as PricingDisplay;
  } catch {
    return PRICING_FALLBACK;
  }
}

export function logPricingEvent(
  event: string,
  tierId: string | null,
  page: string
): void {
  fetch(`${API}/api/public/pricing-event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event, tier_id: tierId, page }),
  }).catch(() => undefined);
}

export function formatComparisonCell(value: string): string {
  if (value === "yes") return "✓";
  if (value === "no") return "—";
  if (value === "partial") return "частично";
  if (value === "limited") return "ограничено";
  if (value === "0") return "—";
  if (value === "∞") return "∞";
  return value;
}
