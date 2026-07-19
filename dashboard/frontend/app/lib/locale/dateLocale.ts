/** BCP-47 locale tags for dates / money display by UI language. */

const DATE_BY_UI: Record<string, string> = {
  de: "de-DE",
  en: "en-GB",
  ru: "ru-RU",
  uk: "uk-UA",
};

export function dateLocaleForUi(uiLang: string | undefined | null): string {
  const code = (uiLang || "de").slice(0, 2).toLowerCase();
  return DATE_BY_UI[code] ?? DATE_BY_UI.de;
}
