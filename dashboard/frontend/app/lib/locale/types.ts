export type {
  AssistantLocale,
  LocaleDefinition,
  LocaleState,
  UiLocale,
} from "./registry";

export {
  DEFAULT_UI_LOCALE,
  ETALON_UI_LOCALES,
  LOCALE_REGISTRY,
  TRANSLATED_UI_LOCALES,
  getLocaleDefinition,
  isEtalonUiLocale,
  isPlatformLocale,
  isRtlLocale,
  isUiLocale,
  localeMatchesQuery,
  normalizeLocaleTag,
  resolveEtalonUiLocale,
  resolveUiLocale,
} from "./registry";

export type { EtalonUiLocale } from "./registry";

/** @deprecated use ETALON_UI_LOCALES / LOCALE_REGISTRY */
export const SUPPORTED_LOCALES = ["ru", "en", "de", "uk"] as const;
