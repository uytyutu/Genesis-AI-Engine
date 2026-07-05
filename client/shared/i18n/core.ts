import type { LocaleId, Messages } from "./types";
import { FALLBACK_LOCALE, resolveLocale } from "./registry";
import de from "./locales/de.json";
import en from "./locales/en.json";
import ru from "./locales/ru.json";

const PACKS: Partial<Record<LocaleId, Messages>> = {
  ru: ru as Messages,
  en: en as Messages,
  de: de as Messages,
};

export function messagesFor(locale: LocaleId): Messages {
  return PACKS[locale] ?? PACKS[FALLBACK_LOCALE] ?? (en as Messages);
}

export function t(
  locale: LocaleId,
  key: string,
  vars?: Record<string, string | number>,
): string {
  const pack = messagesFor(locale);
  const fallback = messagesFor(FALLBACK_LOCALE);
  let text = pack[key] ?? fallback[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      text = text.split(`{{${k}}}`).join(String(v));
    }
  }
  return text;
}

export function normalizeLocale(raw: string | null | undefined): LocaleId {
  return resolveLocale(raw);
}
