"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  LOCALES,
  resolveLocale,
  t as translate,
  type Locale,
} from "@/lib/i18n/dictionaries";
import {
  detectBrowserLocale,
  persistLocale,
  readStoredLocale,
} from "@/lib/i18n/core";

type Ctx = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  locales: typeof LOCALES;
};

const I18nContext = createContext<Ctx | null>(null);

function readClientLocale(initialLocale?: string): Locale {
  const stored = readStoredLocale();
  if (stored) return stored;
  if (initialLocale) return resolveLocale(initialLocale);
  return detectBrowserLocale();
}

export function I18nProvider({
  children,
  initialLocale,
}: {
  children: React.ReactNode;
  initialLocale?: string;
}) {
  const [locale, setLocaleState] = useState<Locale>(() =>
    typeof window === "undefined"
      ? resolveLocale(initialLocale)
      : readClientLocale(initialLocale)
  );

  useEffect(() => {
    setLocaleState(readClientLocale(initialLocale));
  }, [initialLocale]);

  useEffect(() => {
    persistLocale(locale);
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    persistLocale(l);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      translate(locale, key, vars),
    [locale]
  );

  const value = useMemo(
    () => ({ locale, setLocale, t, locales: LOCALES }),
    [locale, setLocale, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n outside provider");
  return ctx;
}
