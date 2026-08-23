"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { I18nextProvider } from "react-i18next";

import { ensureI18n } from "../lib/i18n/client";
import { detectBrowserLocale } from "../lib/locale/detect";
import { getLocaleDefinition, isRtlLocale } from "../lib/locale/registry";
import {
  defaultLocaleState,
  loadLocaleState,
  persistLocaleState,
} from "../lib/locale/storage";
import type { AssistantLocale, LocaleState, UiLocale } from "../lib/locale/types";

type LocaleContextValue = LocaleState & {
  setAutoDetect: (auto: boolean) => void;
  setUiLocale: (locale: UiLocale) => void;
  setAssistantLocale: (locale: AssistantLocale) => void;
  /** One atomic write — use from public language chips. */
  applyUiLocale: (locale: UiLocale) => void;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({
  children,
  initialLocale,
  localeFromCookie = false,
}: {
  children: ReactNode;
  /** From cookie in root layout — keeps SSR HTML language aligned with client. */
  initialLocale?: UiLocale;
  localeFromCookie?: boolean;
}) {
  const [state, setState] = useState<LocaleState>(() =>
    defaultLocaleState(initialLocale, { fromCookie: localeFromCookie }),
  );
  const [hydrated, setHydrated] = useState(false);
  const i18n = useMemo(() => ensureI18n(state.uiLocale), [state.uiLocale]);

  const commit = useCallback(
    (next: LocaleState) => {
      setState(next);
      persistLocaleState(next);
      void i18n.changeLanguage(next.uiLocale);
    },
    [i18n],
  );

  // After mount: sync storage. Never call changeLanguage when uiLocale is unchanged —
  // that re-notifies every useTranslation consumer and flickers the whole storefront.
  useEffect(() => {
    setHydrated(true);
    const loaded = loadLocaleState();
    if (
      loaded.uiLocale === state.uiLocale &&
      loaded.assistantLocale === state.assistantLocale
    ) {
      if (loaded.autoDetect !== state.autoDetect) {
        setState((prev) => ({ ...prev, autoDetect: loaded.autoDetect }));
      }
      persistLocaleState({
        ...loaded,
        uiLocale: state.uiLocale,
        assistantLocale: state.assistantLocale,
      });
      return;
    }
    commit(loaded);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const def = getLocaleDefinition(state.uiLocale);
    document.documentElement.lang = state.uiLocale;
    document.documentElement.dir = isRtlLocale(state.uiLocale) ? "rtl" : "ltr";
    if (def?.rtl) {
      document.documentElement.setAttribute("data-locale-rtl", "1");
    } else {
      document.documentElement.removeAttribute("data-locale-rtl");
    }
  }, [state.uiLocale]);

  const setAutoDetect = useCallback(
    (auto: boolean) => {
      setState((prev) => {
        const uiLocale = auto ? detectBrowserLocale() : prev.uiLocale;
        const next: LocaleState = {
          autoDetect: auto,
          uiLocale,
          assistantLocale: auto ? uiLocale : prev.assistantLocale,
        };
        persistLocaleState(next);
        void i18n.changeLanguage(next.uiLocale);
        return next;
      });
    },
    [i18n],
  );

  const setUiLocale = useCallback(
    (uiLocale: UiLocale) => {
      setState((prev) => {
        const next: LocaleState = {
          autoDetect: false,
          uiLocale,
          assistantLocale:
            prev.assistantLocale === prev.uiLocale ? uiLocale : prev.assistantLocale,
        };
        persistLocaleState(next);
        void i18n.changeLanguage(next.uiLocale);
        return next;
      });
    },
    [i18n],
  );

  const setAssistantLocale = useCallback((assistantLocale: AssistantLocale) => {
    setState((prev) => {
      const next: LocaleState = { ...prev, autoDetect: false, assistantLocale };
      persistLocaleState(next);
      return next;
    });
  }, []);

  const applyUiLocale = useCallback(
    (uiLocale: UiLocale) => {
      const next: LocaleState = {
        autoDetect: false,
        uiLocale,
        assistantLocale: uiLocale,
      };
      commit(next);
    },
    [commit],
  );

  const value = useMemo(
    () => ({
      ...state,
      setAutoDetect,
      setUiLocale,
      setAssistantLocale,
      applyUiLocale,
    }),
    [state, setAutoDetect, setUiLocale, setAssistantLocale, applyUiLocale],
  );

  return (
    <LocaleContext.Provider value={value}>
      <I18nextProvider i18n={i18n}>
        {/* Hide translated chrome until hydrated when no cookie yet — rare flash only */}
        <div
          suppressHydrationWarning
          data-locale-hydrated={hydrated ? "1" : "0"}
        >
          {children}
        </div>
      </I18nextProvider>
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error("useLocale must be used within LocaleProvider");
  }
  return ctx;
}
