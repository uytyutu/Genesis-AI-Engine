/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Digital Company";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = ASSISTANT_NAME;

export const PUBLIC_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — ваш цифровой руководитель в ${BRAND_NAME}. Что делаем первым — проект, документ или сайт?`;

export function brandSignatureLines(includeTagline = false): string[] {
  if (includeTagline) {
    return [ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE];
  }
  return [ASSISTANT_NAME, BRAND_SIGNATURE];
}
