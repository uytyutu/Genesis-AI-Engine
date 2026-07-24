/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Digital Company";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = ASSISTANT_NAME;

export const PUBLIC_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — ваш цифровой сотрудник в ${BRAND_NAME}.\n\nРасскажите идею, вопрос по бизнесу или задачу — обсудим свободно, как в обычном чате. Когда понадобится хранить материалы, я сам предложу оформить это как проект.`;

/** /site hub — ownership first, project second. */
export const PUBLIC_SITE_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME}.\n\nЯ цифровой менеджер ${BRAND_NAME}: сайты (Basic / Business / Premium), анализ и ремонт, автоматизация.\n\nНапишите задачу — например «хочу сайт» или «отремонтировать сайт» — и я сразу предложу следующий шаг.`;

export function publicLeadCaptureWelcome(nicheLabel: string): string {
  return (
    `Здравствуйте! Я ${ASSISTANT_NAME}.\n\n` +
    `Опишите проблему — я оформлю заявку для ${nicheLabel.toLowerCase()}. ` +
    `Город, срочность и контакт можно написать в одном сообщении. Без анкеты.`
  );
}

export function brandSignatureLines(includeTagline = false): string[] {
  if (includeTagline) {
    return [ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE];
  }
  return [ASSISTANT_NAME, BRAND_SIGNATURE];
}
