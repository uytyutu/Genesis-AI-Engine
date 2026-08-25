import { detectBrowserLocale } from "./detect";
import {
  DEFAULT_UI_LOCALE,
  isPlatformLocale,
  resolveEtalonUiLocale,
  type LocaleState,
  type UiLocale,
} from "./types";

const AUTO_KEY = "virtus_ui_locale_auto";
const UI_KEY = "virtus_ui_locale";
/** @deprecated L0 — removed as competing SSOT; cleared on persist */
const ASSISTANT_KEY_LEGACY = "virtus_assistant_locale";
/** Cookie mirrors UI locale so SSR HTML matches client (stops Angebot≠Предложение). */
export const UI_LOCALE_COOKIE = "virtus_ui_locale";

function readAuto(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = localStorage.getItem(AUTO_KEY);
    if (raw === "0") return false;
    if (raw === "1") return true;
  } catch {
    /* private mode */
  }
  return false;
}

function readStoredUi(): UiLocale | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(UI_KEY);
    return isPlatformLocale(raw) ? resolveEtalonUiLocale(raw) : null;
  } catch {
    return null;
  }
}

function writeLocaleCookie(uiLocale: UiLocale): void {
  if (typeof document === "undefined") return;
  try {
    const maxAge = 60 * 60 * 24 * 365;
    document.cookie = `${UI_LOCALE_COOKIE}=${encodeURIComponent(uiLocale)}; path=/; max-age=${maxAge}; samesite=lax`;
  } catch {
    /* ignore */
  }
}

/**
 * Hydration-safe seed — identical on server and first client paint when cookie matches.
 */
export function defaultLocaleState(
  initialLocale?: UiLocale,
  options?: { fromCookie?: boolean },
): LocaleState {
  void options?.fromCookie;
  const uiLocale =
    initialLocale && isPlatformLocale(initialLocale)
      ? resolveEtalonUiLocale(initialLocale)
      : DEFAULT_UI_LOCALE;
  return {
    autoDetect: false,
    uiLocale,
  };
}

/**
 * Browser-only locale after mount. Safe to use navigator + localStorage.
 *
 * L0 rules:
 * - Stored uiLocale wins (manual choice never silently reset).
 * - First visit (no store): browser → etalon de/en/ru/uk, else DE.
 * - autoDetect=true: follow browser (etalon) until user picks manually.
 */
export function loadLocaleState(): LocaleState {
  if (typeof window === "undefined") {
    return defaultLocaleState();
  }
  const autoDetect = readAuto();
  const storedUi = readStoredUi();
  if (storedUi && !autoDetect) {
    return { uiLocale: storedUi, autoDetect: false };
  }
  if (autoDetect) {
    return { uiLocale: detectBrowserLocale(), autoDetect: true };
  }
  // First visit — browser detect into etalon, else DE.
  const uiLocale = storedUi ?? detectBrowserLocale();
  return { uiLocale, autoDetect: false };
}

export function persistLocaleState(state: LocaleState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(AUTO_KEY, state.autoDetect ? "1" : "0");
    localStorage.setItem(UI_KEY, state.uiLocale);
    writeLocaleCookie(state.uiLocale);
    // L0: drop competing assistant locale key
    localStorage.removeItem(ASSISTANT_KEY_LEGACY);
  } catch {
    /* private mode */
  }
}
