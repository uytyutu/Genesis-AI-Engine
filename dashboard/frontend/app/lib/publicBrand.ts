/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Digital Company";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = ASSISTANT_NAME;

export const PUBLIC_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.\n\nПришлите бизнес-план или кратко опишите нишу — разберу рынок и предложу подходящий пакет услуг (Basic / Business / Premium, AI Bot и др.). Сам сайты не собираю и не редактирую — только анализ и рекомендация, затем ссылка на заявку.`;

/** /site hub — ownership first, project second. */
export const PUBLIC_SITE_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.\n\nОпишите нишу или приложите бизнес-план — подскажу пакет под ваш бизнес. Данные не передаём третьим лицам.`;

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
