"use client";

import officeDe from "../office/i18n/de.json";
import officeEn from "../office/i18n/en.json";
import officeUk from "../office/i18n/uk.json";
import officeRu from "../office/i18n/ru.json";
import officePl from "../office/i18n/pl.json";
import officeTr from "../office/i18n/tr.json";
import officeFr from "../office/i18n/fr.json";
import officeEs from "../office/i18n/es.json";
import officeIt from "../office/i18n/it.json";

export const OFFICE_I18N_LOCALES = [
  "de",
  "en",
  "uk",
  "ru",
  "pl",
  "tr",
  "fr",
  "es",
  "it",
] as const;

export type OfficeI18nLocale = (typeof OFFICE_I18N_LOCALES)[number];

export const OFFICE_I18N_BUNDLES: Record<OfficeI18nLocale, Record<string, unknown>> = {
  de: officeDe as Record<string, unknown>,
  en: officeEn as Record<string, unknown>,
  uk: officeUk as Record<string, unknown>,
  ru: officeRu as Record<string, unknown>,
  pl: officePl as Record<string, unknown>,
  tr: officeTr as Record<string, unknown>,
  fr: officeFr as Record<string, unknown>,
  es: officeEs as Record<string, unknown>,
  it: officeIt as Record<string, unknown>,
};

export function resolveOfficeI18nLocale(code: string | undefined | null): OfficeI18nLocale {
  const c = (code || "de").toLowerCase().split("-")[0];
  if ((OFFICE_I18N_LOCALES as readonly string[]).includes(c)) {
    return c as OfficeI18nLocale;
  }
  return "de";
}
