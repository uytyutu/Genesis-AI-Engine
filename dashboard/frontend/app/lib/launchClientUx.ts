/**
 * Launch Client UX — purchase routes + price hints (SSOT for empty cabinet).
 * Must match commercialCatalog / PUBLIC_LANDING_MIN_EUR.
 */

export const LAUNCH_PURCHASE_ROUTES = {
  website: "/order?form=1",
  shop: "/order/shop",
  ai: "/order/bot",
} as const;

export const LAUNCH_PRICE_HINTS = {
  website: "ab 299 €",
  shop: "ab 799 €",
  ai: "ab 499 €",
} as const;
