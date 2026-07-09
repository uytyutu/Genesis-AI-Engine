export const SUPPORTED_LOCALES = ["ru", "en", "de"] as const;

export type UiLocale = (typeof SUPPORTED_LOCALES)[number];
export type AssistantLocale = UiLocale;

export type LocaleState = {
  uiLocale: UiLocale;
  assistantLocale: AssistantLocale;
  autoDetect: boolean;
};

/**
 * Product fallback locale (R1-B policy):
 * - unsupported browser language tags → this locale;
 * - missing i18n keys → same locale via i18next `fallbackLng`;
 * - manual mode with empty storage → this locale.
 *
 * English is the international default for Virtus Core public layer.
 */
export const DEFAULT_UI_LOCALE: UiLocale = "en";

export function isUiLocale(value: string | null | undefined): value is UiLocale {
  return SUPPORTED_LOCALES.includes(value as UiLocale);
}
