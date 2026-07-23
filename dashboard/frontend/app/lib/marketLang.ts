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

/** When the buyer picks a UI language, use this market for Path A prices/currency. */
export const LANG_CANONICAL_MARKET: Record<string, string> = {
  de: "DE",
  en: "US",
  uk: "UA",
  ru: "RU",
  fr: "FR",
  nl: "NL",
  es: "ES",
  it: "IT",
  pt: "PT",
  pl: "PL",
  cs: "CZ",
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

/** Invert market→lang for LanguageSwitcher on /site (en → US, de → DE, …). */
export function canonicalMarketForLang(lang: string | null | undefined): string {
  const code = (lang || "de").slice(0, 2).toLowerCase();
  return LANG_CANONICAL_MARKET[code] || "DE";
}
