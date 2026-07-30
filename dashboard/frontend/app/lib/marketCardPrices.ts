/**
 * Market Resolver (frontend) — hub card prices from /api/public/pricing.
 * Amounts/currency/symbol are backend SSOT; UI only adds localized prefixes.
 */

export type HubCardPrices = {
  market_code: string;
  currency: string;
  symbol: string;
  landing_website: {
    range_label: string;
    basic_label?: string;
    premium_label?: string;
  };
  ai_business_bot: {
    setup_label: string;
    monthly_label: string;
  };
  website_repair: {
    from_label: string;
  };
  website_check?: { free?: boolean };
};

export type HubPriceCopy = {
  /** Localized "from" / "od" / "ab" / … */
  priceFrom: string;
  /** Localized "monthly" suffix after "+". */
  monthly: string;
  /** Localized free label for website_check. */
  free: string;
};

/** Compose display labels for ServiceCatalog cards. */
export function composeHubCardPriceLabels(
  hub: HubCardPrices | null | undefined,
  copy: HubPriceCopy,
): Record<string, string> {
  if (!hub?.landing_website?.range_label) {
    return {};
  }
  const from = (copy.priceFrom || "from").trim();
  const monthly = (copy.monthly || "monthly").trim();
  const free = (copy.free || "Free").trim();
  const out: Record<string, string> = {
    landing_website: hub.landing_website.range_label,
    website_check: free,
  };
  if (hub.ai_business_bot?.setup_label) {
    out.ai_business_bot = `${from} ${hub.ai_business_bot.setup_label} + ${monthly}`;
  }
  if (hub.website_repair?.from_label) {
    out.website_repair = `${from} ${hub.website_repair.from_label}`;
  }
  return out;
}
