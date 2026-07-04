import type { ThemeMode } from "./tokens";

const STORAGE_KEY = "genesis.client.settings.v1";

export type AppSettings = {
  apiUrl: string;
  theme: ThemeMode;
  /** Stage 1 scaffold — reserved for owner/session auth */
  apiKey: string;
  checkUpdatesOnLaunch: boolean;
};

export const DEFAULT_API_URL =
  import.meta.env.VITE_GENESIS_API_URL ??
  "https://genesis-ai-engine-production.up.railway.app";

export const defaultSettings = (): AppSettings => ({
  apiUrl: DEFAULT_API_URL,
  theme: "dark",
  apiKey: "",
  checkUpdatesOnLaunch: true,
});

export function loadSettings(): AppSettings {
  if (typeof localStorage === "undefined") return defaultSettings();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultSettings();
    return { ...defaultSettings(), ...JSON.parse(raw) };
  } catch {
    return defaultSettings();
  }
}

export function saveSettings(settings: AppSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}
