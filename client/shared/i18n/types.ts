/** Genesis i18n — shared across Desktop, Web, Mobile. */

export const LOCALE_IDS = [
  "ru",
  "en",
  "de",
  "uk",
  "fr",
  "es",
  "it",
  "pt",
  "pl",
  "tr",
  "ar",
  "fa",
  "hi",
  "zh-Hans",
  "zh-Hant",
  "ja",
  "ko",
] as const;

export type LocaleId = (typeof LOCALE_IDS)[number];

/** CEO Desktop settings — fully translated packs today. */
export const CEO_DESKTOP_LOCALES: LocaleId[] = ["ru", "en", "de"];

export type LocaleMeta = {
  id: LocaleId;
  label: string;
  nativeName: string;
  dir: "ltr" | "rtl";
  /** Translation pack available (not just fallback). */
  packReady: boolean;
};

export type Messages = Record<string, string>;
