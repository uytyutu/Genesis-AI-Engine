import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  defaultSettings,
  loadSettings,
  saveSettings,
  type AppSettings,
} from "../lib/settings";
import type { ThemeMode } from "../lib/tokens";

type AppSettingsContextValue = {
  settings: AppSettings;
  updateSettings: (patch: Partial<AppSettings>) => void;
  resetSettings: () => void;
  resolvedTheme: "dark" | "light";
};

const AppSettingsContext = createContext<AppSettingsContextValue | null>(null);

function resolveTheme(theme: ThemeMode): "dark" | "light" {
  if (theme === "system" && typeof window !== "undefined") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  return theme === "light" ? "light" : "dark";
}

export function AppSettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(() => loadSettings());
  const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light">(() =>
    resolveTheme(settings.theme),
  );

  const updateSettings = useCallback((patch: Partial<AppSettings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      saveSettings(next);
      return next;
    });
  }, []);

  const resetSettings = useCallback(() => {
    const next = defaultSettings();
    saveSettings(next);
    setSettings(next);
  }, []);

  useEffect(() => {
    setResolvedTheme(resolveTheme(settings.theme));
    document.documentElement.dataset.theme = resolveTheme(settings.theme);

    if (settings.theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const resolved = resolveTheme("system");
      setResolvedTheme(resolved);
      document.documentElement.dataset.theme = resolved;
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [settings.theme]);

  const value = useMemo(
    () => ({ settings, updateSettings, resetSettings, resolvedTheme }),
    [settings, updateSettings, resetSettings, resolvedTheme],
  );

  return (
    <AppSettingsContext.Provider value={value}>
      {children}
    </AppSettingsContext.Provider>
  );
}

export function useAppSettings(): AppSettingsContextValue {
  const ctx = useContext(AppSettingsContext);
  if (!ctx) throw new Error("useAppSettings outside provider");
  return ctx;
}
