"use client";

import { useCallback, useMemo } from "react";
import { useLocale } from "../context/LocaleContext";
import {
  OFFICE_I18N_BUNDLES,
  resolveOfficeI18nLocale,
  type OfficeI18nLocale,
} from "./officeI18n";
import type { UiLocale } from "./locale/types";

type Dict = Record<string, unknown>;

function getPath(obj: Dict, path: string): unknown {
  return path.split(".").reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && key in (acc as Dict)) {
      return (acc as Dict)[key];
    }
    return undefined;
  }, obj);
}

function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (_, k: string) =>
    vars[k] !== undefined ? String(vars[k]) : `{{${k}}}`,
  );
}

export function useOfficeT() {
  const { uiLocale, applyUiLocale } = useLocale();
  const locale = resolveOfficeI18nLocale(uiLocale);
  const dict = OFFICE_I18N_BUNDLES[locale] as Dict;
  const fallback = OFFICE_I18N_BUNDLES.de as Dict;
  const english = OFFICE_I18N_BUNDLES.en as Dict;

  const t = useCallback(
    (path: string, vars?: Record<string, string | number>) => {
      let raw = getPath(dict, path);
      // Bewerbung / preview leftover English in non-EN locales → use German client copy
      if (
        locale !== "en" &&
        locale !== "de" &&
        typeof raw === "string" &&
        (path === "bewerbung" ||
          path.startsWith("bewerbung.") ||
          path === "preview" ||
          path.startsWith("preview.") ||
          path === "documentLanguage" ||
          path === "cvTargetMarket")
      ) {
        const enVal = getPath(english, path);
        if (typeof enVal === "string" && raw === enVal) {
          raw = getPath(fallback, path);
        }
      }
      if (raw === undefined) {
        raw = getPath(fallback, path);
      }
      if (typeof raw !== "string") {
        const fallbackStr =
          vars && typeof vars.defaultValue === "string" ? vars.defaultValue : path;
        return interpolate(fallbackStr, vars);
      }
      return interpolate(raw, vars);
    },
    [dict, fallback, english, locale],
  );

  const setOfficeLocale = useCallback(
    (code: OfficeI18nLocale) => {
      applyUiLocale(code as UiLocale);
    },
    [applyUiLocale],
  );

  return useMemo(
    () => ({ t, locale, setOfficeLocale, dict }),
    [t, locale, setOfficeLocale, dict],
  );
}
