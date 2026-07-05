import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import { t as translate } from "@genesis/i18n/core";
import { LOCALE_REGISTRY, resolveLocale } from "@genesis/i18n/registry";
import type { LocaleId, LocaleMeta } from "@genesis/i18n/types";

type I18nContextValue = {
  locale: LocaleId;
  meta: LocaleMeta;
  setLocale: (locale: LocaleId) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

type I18nProviderProps = {
  locale: LocaleId;
  onLocaleChange?: (locale: LocaleId) => void;
  children: ReactNode;
};

export function I18nProvider({
  locale: localeProp,
  onLocaleChange,
  children,
}: I18nProviderProps) {
  const locale = resolveLocale(localeProp);
  const meta = LOCALE_REGISTRY[locale];

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = meta.dir;
  }, [locale, meta.dir]);

  const setLocale = useCallback(
    (next: LocaleId) => {
      onLocaleChange?.(resolveLocale(next));
    },
    [onLocaleChange],
  );

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      translate(locale, key, vars),
    [locale],
  );

  const value = useMemo(
    () => ({ locale, meta, setLocale, t }),
    [locale, meta, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n outside I18nProvider");
  return ctx;
}
