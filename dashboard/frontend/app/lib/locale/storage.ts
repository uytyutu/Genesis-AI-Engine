import { detectBrowserLocale } from "./detect";
import {
  DEFAULT_UI_LOCALE,
  isPlatformLocale,
  type AssistantLocale,
  type LocaleState,
  type UiLocale,
} from "./types";

const AUTO_KEY = "virtus_ui_locale_auto";
const UI_KEY = "virtus_ui_locale";
const ASSISTANT_KEY = "virtus_assistant_locale";
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
  // Prefer German storefront until the visitor explicitly enables auto-detect
  // or picks another language (uk / ru / en / EU+CIS list).
  return false;
}

function readStoredUi(): UiLocale | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(UI_KEY);
    return isPlatformLocale(raw) ? raw : null;
  } catch {
    return null;
  }
}

function readStoredAssistant(): AssistantLocale | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(ASSISTANT_KEY);
    return isPlatformLocale(raw) ? raw : null;
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
  const fromCookie = Boolean(options?.fromCookie);
  const uiLocale =
    initialLocale && isPlatformLocale(initialLocale)
      ? initialLocale
      : DEFAULT_UI_LOCALE;
  return {
    // Cookie = explicit prior choice (or last persist). No cookie → still allow auto-detect after mount.
    autoDetect: !fromCookie,
    uiLocale,
    assistantLocale: uiLocale,
  };
}

/**
 * Browser-only locale after mount. Safe to use navigator + localStorage.
 */
export function loadLocaleState(): LocaleState {
  if (typeof window === "undefined") {
    return defaultLocaleState();
  }
  const autoDetect = readAuto();
  const storedUi = readStoredUi();
  const uiLocale = autoDetect
    ? detectBrowserLocale()
    : storedUi ?? DEFAULT_UI_LOCALE;
  const assistantLocale = readStoredAssistant() ?? uiLocale;
  return { uiLocale, assistantLocale, autoDetect };
}

export function persistLocaleState(state: LocaleState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(AUTO_KEY, state.autoDetect ? "1" : "0");
    localStorage.setItem(UI_KEY, state.uiLocale);
    localStorage.setItem(ASSISTANT_KEY, state.assistantLocale);
    writeLocaleCookie(state.uiLocale);
  } catch {
    /* private mode */
  }
}
