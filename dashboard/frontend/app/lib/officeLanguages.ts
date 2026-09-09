/** Full Office translation language catalog — mirrors backend language_catalog.py */

export type OfficeLangOption = {
  code: string;
  label_de: string;
  label_en: string;
  native: string;
};

/** Fallback when API has not loaded yet — must stay in sync with OFFICE_LANGUAGE_CATALOG. */
export const OFFICE_LANGUAGE_CATALOG: readonly OfficeLangOption[] = [
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
] as const;

export function resolveOfficeLanguages(
  fromJob?: Array<Partial<OfficeLangOption>> | null,
  fromApi?: Array<Partial<OfficeLangOption>> | null,
): OfficeLangOption[] {
  const pick = (rows: Array<Partial<OfficeLangOption>> | null | undefined) => {
    if (!rows?.length || rows.length < 5) return null;
    return rows
      .map((r) => ({
        code: String(r.code || "").toLowerCase(),
        label_de: String(r.label_de || r.native || r.code || ""),
        label_en: String(r.label_en || r.native || r.code || ""),
        native: String(r.native || r.label_en || r.label_de || r.code || ""),
      }))
      .filter((r) => r.code);
  };
  return (
    pick(fromApi) ||
    pick(fromJob) ||
    OFFICE_LANGUAGE_CATALOG.map((r) => ({ ...r }))
  );
}
