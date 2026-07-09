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

function readAuto(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const raw = localStorage.getItem(AUTO_KEY);
    if (raw === "0") return false;
    if (raw === "1") return true;
  } catch {
    /* private mode */
  }
  return true;
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

export function loadLocaleState(): LocaleState {
  const autoDetect = readAuto();
  const storedUi = readStoredUi();
  const uiLocale = autoDetect ? detectBrowserLocale() : storedUi ?? DEFAULT_UI_LOCALE;
  const assistantLocale = readStoredAssistant() ?? uiLocale;
  return { uiLocale, assistantLocale, autoDetect };
}

export function persistLocaleState(state: LocaleState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(AUTO_KEY, state.autoDetect ? "1" : "0");
    localStorage.setItem(UI_KEY, state.uiLocale);
    localStorage.setItem(ASSISTANT_KEY, state.assistantLocale);
  } catch {
    /* private mode */
  }
}
