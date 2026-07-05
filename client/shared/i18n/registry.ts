import type { LocaleId, LocaleMeta } from "./types";

export const DEFAULT_LOCALE: LocaleId = "ru";
export const FALLBACK_LOCALE: LocaleId = "en";

export const LOCALE_REGISTRY: Record<LocaleId, LocaleMeta> = {
  ru: { id: "ru", label: "Russian", nativeName: "Русский", dir: "ltr", packReady: true },
  en: { id: "en", label: "English", nativeName: "English", dir: "ltr", packReady: true },
  de: { id: "de", label: "German", nativeName: "Deutsch", dir: "ltr", packReady: true },
  uk: { id: "uk", label: "Ukrainian", nativeName: "Українська", dir: "ltr", packReady: false },
  fr: { id: "fr", label: "French", nativeName: "Français", dir: "ltr", packReady: false },
  es: { id: "es", label: "Spanish", nativeName: "Español", dir: "ltr", packReady: false },
  it: { id: "it", label: "Italian", nativeName: "Italiano", dir: "ltr", packReady: false },
  pt: { id: "pt", label: "Portuguese", nativeName: "Português", dir: "ltr", packReady: false },
  pl: { id: "pl", label: "Polish", nativeName: "Polski", dir: "ltr", packReady: false },
  tr: { id: "tr", label: "Turkish", nativeName: "Türkçe", dir: "ltr", packReady: false },
  ar: { id: "ar", label: "Arabic", nativeName: "العربية", dir: "rtl", packReady: false },
  fa: { id: "fa", label: "Persian", nativeName: "فارسی", dir: "rtl", packReady: false },
  hi: { id: "hi", label: "Hindi", nativeName: "हिन्दी", dir: "ltr", packReady: false },
  "zh-Hans": {
    id: "zh-Hans",
    label: "Chinese (Simplified)",
    nativeName: "中文（简体）",
    dir: "ltr",
    packReady: false,
  },
  "zh-Hant": {
    id: "zh-Hant",
    label: "Chinese (Traditional)",
    nativeName: "中文（繁體）",
    dir: "ltr",
    packReady: false,
  },
  ja: { id: "ja", label: "Japanese", nativeName: "日本語", dir: "ltr", packReady: false },
  ko: { id: "ko", label: "Korean", nativeName: "한국어", dir: "ltr", packReady: false },
};

export function resolveLocale(raw: string | null | undefined): LocaleId {
  if (!raw) return DEFAULT_LOCALE;
  const norm = raw.trim().replace("_", "-");
  if (norm in LOCALE_REGISTRY) return norm as LocaleId;
  const base = norm.split("-")[0];
  if (base in LOCALE_REGISTRY) return base as LocaleId;
  return FALLBACK_LOCALE;
}
