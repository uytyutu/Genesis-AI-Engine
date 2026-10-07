import type { Locale } from "./dictionaries";

export const LOCALE_COOKIE = "anon_locale";
export const LOCALE_STORAGE = "anon_locale";

/** Project default + missing-key fallback (per product rule). */
export const DEFAULT_LOCALE: Locale = "ru";
export const FALLBACK_LOCALE: Locale = "ru";

export function parseLocale(input?: string | null): Locale | null {
  if (!input) return null;
  const base = input.toLowerCase().slice(0, 2);
  const allowed = ["en", "de", "ru", "uk", "pl", "fr", "es", "it", "pt", "nl", "tr", "cs"];
  return (allowed.includes(base) ? base : null) as Locale | null;
}

export function detectBrowserLocale(): Locale {
  if (typeof navigator === "undefined") return DEFAULT_LOCALE;
  return parseLocale(navigator.language) || DEFAULT_LOCALE;
}

export function readStoredLocale(): Locale | null {
  if (typeof window === "undefined") return null;
  try {
    return parseLocale(localStorage.getItem(LOCALE_STORAGE));
  } catch {
    return null;
  }
}

export function persistLocale(locale: Locale) {
  if (typeof document !== "undefined") {
    document.documentElement.lang = locale;
    document.cookie = `${LOCALE_COOKIE}=${locale};path=/;max-age=${60 * 60 * 24 * 365};samesite=lax`;
  }
  if (typeof localStorage !== "undefined") {
    try {
      localStorage.setItem(LOCALE_STORAGE, locale);
    } catch {
      /* private mode */
    }
  }
}
