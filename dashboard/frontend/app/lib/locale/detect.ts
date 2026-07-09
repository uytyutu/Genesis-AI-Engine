import { DEFAULT_UI_LOCALE, isUiLocale, type UiLocale } from "./types";

/** Map browser language tag to supported UI locale. */
export function detectBrowserLocale(): UiLocale {
  if (typeof navigator === "undefined") return DEFAULT_UI_LOCALE;
  const tags = [navigator.language, ...(navigator.languages ?? [])];
  for (const tag of tags) {
    const base = tag.split("-")[0]?.toLowerCase();
    if (isUiLocale(base)) return base;
  }
  if (tags.some((t) => t.toLowerCase().startsWith("de"))) return "de";
  if (tags.some((t) => t.toLowerCase().startsWith("en"))) return "en";
  return DEFAULT_UI_LOCALE;
}
