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
import { loadLocaleState, persistLocaleState } from "../lib/locale/storage";
import type { AssistantLocale, LocaleState, UiLocale } from "../lib/locale/types";

type LocaleContextValue = LocaleState & {
  setAutoDetect: (auto: boolean) => void;
  setUiLocale: (locale: UiLocale) => void;
  setAssistantLocale: (locale: AssistantLocale) => void;
  /** One atomic write — use from public language chips. */
  applyUiLocale: (locale: UiLocale) => void;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LocaleState>(() => loadLocaleState());
  const i18n = useMemo(() => ensureI18n(state.uiLocale), [state.uiLocale]);

  const commit = useCallback(
    (next: LocaleState) => {
      setState(next);
      persistLocaleState(next);
      void i18n.changeLanguage(next.uiLocale);
    },
    [i18n],
  );

  // Re-apply browser locale after mount when auto-detect is on.
  useEffect(() => {
    if (!state.autoDetect) return;
    const browser = detectBrowserLocale();
    if (browser === state.uiLocale) return;
    commit({
      autoDetect: true,
      uiLocale: browser,
      assistantLocale: browser,
    });
  }, [state.autoDetect, state.uiLocale, commit]);

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
          // Public chips use applyUiLocale (UI+assistant together). Full panel may
          // keep assistant separate until the user changes it too.
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

  const setAssistantLocale = useCallback(
    (assistantLocale: AssistantLocale) => {
      setState((prev) => {
        const next: LocaleState = { ...prev, autoDetect: false, assistantLocale };
        persistLocaleState(next);
        return next;
      });
    },
    [],
  );

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
      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
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
