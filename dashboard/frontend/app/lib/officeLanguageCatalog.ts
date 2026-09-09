/** Full Virtus Office document translation language catalog (matches backend language_catalog.py). */
import type { OfficeLanguage } from "./officeApi";

export const OFFICE_DOCUMENT_LANGUAGES: OfficeLanguage[] = [
  { code: "de", label_de: "Deutsch", label_en: "German", native: "Deutsch" },
  { code: "en", label_de: "Englisch", label_en: "English", native: "English" },
  { code: "uk", label_de: "Ukrainisch", label_en: "Ukrainian", native: "Українська" },
  { code: "ru", label_de: "Russisch", label_en: "Russian", native: "Русский" },
  { code: "pl", label_de: "Polnisch", label_en: "Polish", native: "Polski" },
  { code: "fr", label_de: "Französisch", label_en: "French", native: "Français" },
  { code: "es", label_de: "Spanisch", label_en: "Spanish", native: "Español" },
  { code: "it", label_de: "Italienisch", label_en: "Italian", native: "Italiano" },
  { code: "pt", label_de: "Portugiesisch", label_en: "Portuguese", native: "Português" },
  { code: "nl", label_de: "Niederländisch", label_en: "Dutch", native: "Nederlands" },
  { code: "tr", label_de: "Türkisch", label_en: "Turkish", native: "Türkçe" },
  { code: "cs", label_de: "Tschechisch", label_en: "Czech", native: "Čeština" },
  { code: "sk", label_de: "Slowakisch", label_en: "Slovak", native: "Slovenčina" },
  { code: "hu", label_de: "Ungarisch", label_en: "Hungarian", native: "Magyar" },
  { code: "ro", label_de: "Rumänisch", label_en: "Romanian", native: "Română" },
  { code: "bg", label_de: "Bulgarisch", label_en: "Bulgarian", native: "Български" },
  { code: "el", label_de: "Griechisch", label_en: "Greek", native: "Ελληνικά" },
  { code: "hr", label_de: "Kroatisch", label_en: "Croatian", native: "Hrvatski" },
  { code: "sr", label_de: "Serbisch", label_en: "Serbian", native: "Srpski" },
  { code: "sl", label_de: "Slowenisch", label_en: "Slovenian", native: "Slovenščina" },
  { code: "sv", label_de: "Schwedisch", label_en: "Swedish", native: "Svenska" },
  { code: "da", label_de: "Dänisch", label_en: "Danish", native: "Dansk" },
  { code: "no", label_de: "Norwegisch", label_en: "Norwegian", native: "Norsk" },
  { code: "fi", label_de: "Finnisch", label_en: "Finnish", native: "Suomi" },
  { code: "et", label_de: "Estnisch", label_en: "Estonian", native: "Eesti" },
  { code: "lv", label_de: "Lettisch", label_en: "Latvian", native: "Latviešu" },
  { code: "lt", label_de: "Litauisch", label_en: "Lithuanian", native: "Lietuvių" },
  { code: "ar", label_de: "Arabisch", label_en: "Arabic", native: "العربية" },
  { code: "he", label_de: "Hebräisch", label_en: "Hebrew", native: "עברית" },
  { code: "zh", label_de: "Chinesisch", label_en: "Chinese", native: "中文" },
  { code: "ja", label_de: "Japanisch", label_en: "Japanese", native: "日本語" },
  { code: "ko", label_de: "Koreanisch", label_en: "Korean", native: "한국어" },
  { code: "hi", label_de: "Hindi", label_en: "Hindi", native: "हिन्दी" },
];

export function mergeOfficeLanguages(fromApi?: OfficeLanguage[] | null): OfficeLanguage[] {
  if (fromApi && fromApi.length >= OFFICE_DOCUMENT_LANGUAGES.length) {
    return fromApi;
  }
  if (fromApi && fromApi.length > 0) {
    const byCode = new Map(OFFICE_DOCUMENT_LANGUAGES.map((l) => [l.code, l]));
    for (const row of fromApi) {
      if (row?.code) byCode.set(row.code, { ...byCode.get(row.code), ...row });
    }
    return Array.from(byCode.values());
  }
  return OFFICE_DOCUMENT_LANGUAGES;
}
