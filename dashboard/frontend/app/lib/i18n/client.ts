"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { type UiLocale } from "../locale/types";
import { localeResources } from "./resources";

let initialized = false;

/** Keep i18n.language in sync before React paints (SSR + hydration). */
function applyLanguageSync(uiLocale: UiLocale): void {
  if (i18n.language === uiLocale && i18n.resolvedLanguage === uiLocale) {
    return;
  }
  // changeLanguage is async; set immediately so first paint matches.
  i18n.language = uiLocale;
  (i18n as { resolvedLanguage?: string }).resolvedLanguage = uiLocale;
  void i18n.changeLanguage(uiLocale);
}

export function ensureI18n(uiLocale: UiLocale): typeof i18n {
  if (!initialized) {
    void i18n.use(initReactI18next).init({
      resources: localeResources,
      lng: uiLocale,
      fallbackLng: "de",
      supportedLngs: Object.keys(localeResources),
      nonExplicitSupportedLngs: true,
      defaultNS: "common",
      ns: ["common", "chat", "site", "errors"],
      interpolation: { escapeValue: false },
      react: { useSuspense: false },
    });
    initialized = true;
  } else {
    applyLanguageSync(uiLocale);
  }
  return i18n;
}
