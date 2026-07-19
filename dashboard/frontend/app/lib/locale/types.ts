export type {
  AssistantLocale,
  LocaleDefinition,
  LocaleState,
  UiLocale,
} from "./registry";

export {
  DEFAULT_UI_LOCALE,
  LOCALE_REGISTRY,
  TRANSLATED_UI_LOCALES,
  getLocaleDefinition,
  isPlatformLocale,
  isRtlLocale,
  isUiLocale,
  localeMatchesQuery,
  normalizeLocaleTag,
  resolveUiLocale,
} from "./registry";

/** @deprecated use LOCALE_REGISTRY — kept for legacy imports */
export const SUPPORTED_LOCALES = ["ru", "en", "de", "uk"] as const;
