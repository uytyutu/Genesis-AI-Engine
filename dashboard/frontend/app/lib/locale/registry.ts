/**
 * Global UI locale registry — R4-A.2 platform architecture.
 * Add a language here (+ optional locales/<code>/ JSON later); no code rewrites.
 */

export type LocaleDefinition = {
  code: string;
  nativeName: string;
  englishName: string;
  rtl?: boolean;
  /** Full UI bundle under dashboard/frontend/locales/<code>/ */
  translated?: boolean;
};

export const LOCALE_REGISTRY: readonly LocaleDefinition[] = [
  { code: "en", nativeName: "English", englishName: "English", translated: true },
  { code: "ru", nativeName: "Русский", englishName: "Russian", translated: true },
  { code: "de", nativeName: "Deutsch", englishName: "German", translated: true },
  { code: "uk", nativeName: "Українська", englishName: "Ukrainian", translated: true },
  // Country Desk markets — storefront selectable (EN pack until native JSON ships)
  { code: "cs", nativeName: "Čeština", englishName: "Czech", translated: true },
  { code: "pl", nativeName: "Polski", englishName: "Polish", translated: true },
  { code: "fr", nativeName: "Français", englishName: "French", translated: true },
  { code: "nl", nativeName: "Nederlands", englishName: "Dutch", translated: true },
  { code: "es", nativeName: "Español", englishName: "Spanish", translated: true },
  { code: "it", nativeName: "Italiano", englishName: "Italian", translated: true },
  { code: "pt", nativeName: "Português", englishName: "Portuguese", translated: true },
  { code: "tr", nativeName: "Türkçe", englishName: "Turkish" },
  { code: "sv", nativeName: "Svenska", englishName: "Swedish" },
  { code: "ar", nativeName: "العربية", englishName: "Arabic", rtl: true },
  { code: "fa", nativeName: "فارسی", englishName: "Persian", rtl: true },
  { code: "he", nativeName: "עברית", englishName: "Hebrew", rtl: true },
  { code: "hi", nativeName: "हिन्दी", englishName: "Hindi" },
  { code: "ja", nativeName: "日本語", englishName: "Japanese" },
  { code: "ko", nativeName: "한국어", englishName: "Korean" },
  { code: "zh-Hans", nativeName: "简体中文", englishName: "Chinese (Simplified)" },
  { code: "zh-Hant", nativeName: "繁體中文", englishName: "Chinese (Traditional)" },
] as const;

export type UiLocale = (typeof LOCALE_REGISTRY)[number]["code"];
export type AssistantLocale = UiLocale;

export type LocaleState = {
  uiLocale: UiLocale;
  assistantLocale: AssistantLocale;
  autoDetect: boolean;
};

export const DEFAULT_UI_LOCALE: UiLocale = "de";

const LOCALE_BY_CODE = new Map(LOCALE_REGISTRY.map((def) => [def.code, def]));

/** Browser / BCP-47 tag aliases → registry code */
const TAG_ALIASES: Record<string, UiLocale> = {
  "zh-cn": "zh-Hans",
  "zh-sg": "zh-Hans",
  "zh-tw": "zh-Hant",
  "zh-hk": "zh-Hant",
  "zh-mo": "zh-Hant",
  "pt-br": "pt",
  "pt-pt": "pt",
  "uk-ua": "uk",
  iw: "he",
};

export function getLocaleDefinition(code: string): LocaleDefinition | undefined {
  return LOCALE_BY_CODE.get(code);
}

export function isPlatformLocale(value: string | null | undefined): value is UiLocale {
  return Boolean(value && LOCALE_BY_CODE.has(value));
}

/** @deprecated use isPlatformLocale */
export const isUiLocale = isPlatformLocale;

export function normalizeLocaleTag(raw: string): UiLocale | null {
  const norm = raw.trim().replace(/_/g, "-");
  if (!norm) return null;
  if (LOCALE_BY_CODE.has(norm)) return norm as UiLocale;
  const alias = TAG_ALIASES[norm.toLowerCase()];
  if (alias) return alias;
  const base = norm.split("-")[0]?.toLowerCase();
  if (base && LOCALE_BY_CODE.has(base)) return base as UiLocale;
  return null;
}

export function resolveUiLocale(raw: string | null | undefined): UiLocale {
  if (!raw) return DEFAULT_UI_LOCALE;
  return normalizeLocaleTag(raw) ?? DEFAULT_UI_LOCALE;
}

export function isRtlLocale(code: string): boolean {
  return Boolean(getLocaleDefinition(code)?.rtl);
}

export function localeMatchesQuery(def: LocaleDefinition, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    def.code.toLowerCase().includes(q) ||
    def.nativeName.toLowerCase().includes(q) ||
    def.englishName.toLowerCase().includes(q)
  );
}

export const TRANSLATED_UI_LOCALES = LOCALE_REGISTRY.filter((d) => d.translated).map(
  (d) => d.code,
);
