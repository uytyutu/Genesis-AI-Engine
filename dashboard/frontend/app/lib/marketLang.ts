/** Market code → public storefront / buyer UI language (sync with backend market_delivery). */
export const MARKET_UI_LANG: Record<string, string> = {
  DE: "de",
  AT: "de",
  CH: "de",
  US: "en",
  GB: "en",
  CA: "en",
  AU: "en",
  NZ: "en",
  IE: "en",
  FR: "fr",
  IT: "it",
  ES: "es",
  NL: "nl",
  BE: "nl",
  PT: "pt",
  PL: "pl",
  CZ: "cs",
  SK: "cs",
  RO: "ro",
  UA: "uk",
  RU: "ru",
};

/** Languages we actively sell on Country Desk / Path A. */
export const MARKET_PUBLIC_LANGS = [
  "de",
  "en",
  "uk",
  "ru",
  "cs",
  "pl",
  "fr",
  "nl",
  "es",
  "it",
  "pt",
] as const;

export function uiLangForMarket(market: string | null | undefined): string {
  const code = (market || "DE").toUpperCase();
  return MARKET_UI_LANG[code] || "en";
}
