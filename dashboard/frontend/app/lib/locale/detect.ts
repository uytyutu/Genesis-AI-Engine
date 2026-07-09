import { DEFAULT_UI_LOCALE, normalizeLocaleTag, type UiLocale } from "./types";

/** Pick best UI locale from browser language tags. */
export function detectBrowserLocale(): UiLocale {
  if (typeof navigator === "undefined") return DEFAULT_UI_LOCALE;
  const tags = [navigator.language, ...(navigator.languages ?? [])];
  for (const tag of tags) {
    const resolved = normalizeLocaleTag(tag);
    if (resolved) return resolved;
  }
  return DEFAULT_UI_LOCALE;
}
