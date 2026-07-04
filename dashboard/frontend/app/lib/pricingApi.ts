const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PricingTier = {
  id: string;
  name: string;
  price_eur_month: number | null;
  price_label: string;
  period: string;
  audience: string;
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
  subscriptions: PricingTier[];
  services: PricingService[];
  business_units: BusinessUnit[];
};

export async function fetchPricingDisplay(): Promise<PricingDisplay | null> {
  try {
    const res = await fetch(`${API}/api/public/pricing`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as PricingDisplay;
  } catch {
    return null;
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
