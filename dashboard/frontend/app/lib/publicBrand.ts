/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Intelligent AI Assistant";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = `${ASSISTANT_NAME} Chat`;

export const PUBLIC_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — чем могу помочь?`;

export function brandSignatureLines(includeTagline = false): string[] {
  if (includeTagline) {
    return [ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE];
  }
  return [ASSISTANT_NAME, BRAND_SIGNATURE];
}
