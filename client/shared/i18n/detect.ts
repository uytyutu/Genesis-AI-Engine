import type { LocaleId } from "./types";

/** Lightweight script detection for chat input (mirrors backend heuristics). */
export function detectLocaleFromText(text: string): LocaleId | null {
  const sample = text.trim().slice(0, 400);
  if (!sample) return null;

  if (/[\u0600-\u06FF]/.test(sample)) return "ar";
  if (/[\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/.test(sample)) return "fa";
  if (/[\u3040-\u30FF\u31F0-\u31FF]/.test(sample)) return "ja";
  if (/[\uAC00-\uD7AF]/.test(sample)) return "ko";
  if (/[\u0900-\u097F]/.test(sample)) return "hi";
  if (/[\u4E00-\u9FFF]/.test(sample)) {
    return /[體國臺灣萬與為說這]/.test(sample) ? "zh-Hant" : "zh-Hans";
  }
  if (/[\u0400-\u04FF]/.test(sample)) {
    return /[іїєґІЇЄҐ]/.test(sample) ? "uk" : "ru";
  }

  const lower = sample.toLowerCase();
  if (/\b(der|die|das|und|ich|nicht|wie|was|hallo|guten)\b/.test(lower)) return "de";
  if (/\b(the|what|how|hello|status|please)\b/.test(lower)) return "en";
  if (/\b(что|как|привет|статус|дальше|задач)\b/.test(lower)) return "ru";

  return null;
}

export function effectiveChatLocale(
  uiLocale: LocaleId,
  userMessage: string,
): LocaleId {
  return detectLocaleFromText(userMessage) ?? uiLocale;
}
