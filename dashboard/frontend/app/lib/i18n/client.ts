"use client";

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { type UiLocale } from "../locale/types";
import { localeResources } from "./resources";

let initialized = false;

export function ensureI18n(uiLocale: UiLocale): typeof i18n {
  if (!initialized) {
    void i18n.use(initReactI18next).init({
      resources: localeResources,
      lng: uiLocale,
      fallbackLng: "en",
      supportedLngs: Object.keys(localeResources),
      nonExplicitSupportedLngs: true,
      defaultNS: "common",
      ns: ["common", "chat", "site", "errors"],
      interpolation: { escapeValue: false },
      react: { useSuspense: false },
    });
    initialized = true;
  } else if (i18n.language !== uiLocale) {
    void i18n.changeLanguage(uiLocale);
  }
  return i18n;
}
