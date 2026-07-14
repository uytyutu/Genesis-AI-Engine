import type { ThemeMode } from "./tokens";
import type { LocaleId } from "@genesis/i18n/types";
import { DEFAULT_LOCALE } from "@genesis/i18n/registry";

const STORAGE_KEY = "genesis.client.settings.v3";
const LEGACY_KEY = "genesis.client.settings.v1";

export type AppSettings = {
  apiUrl: string;
  theme: ThemeMode;
  apiKey: string;
  ownerName: string;
  sessionActive: boolean;
  checkUpdatesOnLaunch: boolean;
  locale: LocaleId;
  /** CEO/dev connect — off by default; customer registration is primary. */
  devMode: boolean;
};

export const DEFAULT_API_URL =
  import.meta.env.VITE_GENESIS_API_URL ?? "http://127.0.0.1:8000";

export const defaultSettings = (): AppSettings => ({
  apiUrl: DEFAULT_API_URL,
  theme: "dark",
  apiKey: "",
  ownerName: "",
  sessionActive: false,
  checkUpdatesOnLaunch: true,
  locale: DEFAULT_LOCALE,
  devMode: false,
});

function migrate(raw: Record<string, unknown>): AppSettings {
  const base = defaultSettings();
  return {
    apiUrl: typeof raw.apiUrl === "string" ? raw.apiUrl : base.apiUrl,
    theme: (raw.theme as ThemeMode) ?? base.theme,
    apiKey: typeof raw.apiKey === "string" ? raw.apiKey : base.apiKey,
    ownerName: typeof raw.ownerName === "string" ? raw.ownerName : base.ownerName,
    sessionActive:
      typeof raw.sessionActive === "boolean" ? raw.sessionActive : base.sessionActive,
    checkUpdatesOnLaunch:
      typeof raw.checkUpdatesOnLaunch === "boolean"
        ? raw.checkUpdatesOnLaunch
        : base.checkUpdatesOnLaunch,
    locale:
      typeof raw.locale === "string" ? (raw.locale as LocaleId) : base.locale,
    devMode: typeof raw.devMode === "boolean" ? raw.devMode : base.devMode,
  };
}

export function loadSettings(): AppSettings {
  if (typeof localStorage === "undefined") return defaultSettings();
  try {
    const raw =
      localStorage.getItem(STORAGE_KEY) ??
      localStorage.getItem("genesis.client.settings.v2") ??
      localStorage.getItem(LEGACY_KEY);
    if (!raw) return defaultSettings();
    return migrate(JSON.parse(raw));
  } catch {
    return defaultSettings();
  }
}

export function saveSettings(settings: AppSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}
