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
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<LocaleState>(() => loadLocaleState());
  const i18n = useMemo(() => ensureI18n(state.uiLocale), [state.uiLocale]);

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

  const commit = useCallback((next: LocaleState) => {
    setState(next);
    persistLocaleState(next);
    void i18n.changeLanguage(next.uiLocale);
  }, [i18n]);

  const setAutoDetect = useCallback(
    (auto: boolean) => {
      const uiLocale = auto ? detectBrowserLocale() : state.uiLocale;
      commit({
        autoDetect: auto,
        uiLocale,
        assistantLocale: state.assistantLocale,
      });
    },
    [commit, state.assistantLocale, state.uiLocale],
  );

  const setUiLocale = useCallback(
    (uiLocale: UiLocale) => {
      commit({
        autoDetect: false,
        uiLocale,
        assistantLocale: state.assistantLocale === state.uiLocale ? uiLocale : state.assistantLocale,
      });
    },
    [commit, state.assistantLocale, state.uiLocale],
  );

  const setAssistantLocale = useCallback(
    (assistantLocale: AssistantLocale) => {
      commit({ ...state, autoDetect: false, assistantLocale });
    },
    [commit, state],
  );

  const value = useMemo(
    () => ({
      ...state,
      setAutoDetect,
      setUiLocale,
      setAssistantLocale,
    }),
    [state, setAutoDetect, setUiLocale, setAssistantLocale],
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
