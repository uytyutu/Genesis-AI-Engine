/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Digital Company";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = ASSISTANT_NAME;

export const PUBLIC_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.\n\nРасскажу о продуктах и услугах, ценах и защите данных (мы никому не передаём ваши данные). Сам файлы и сайты не выдаю — только ссылки на форму заказа или поддержку.\n\nСпросите, например: «какие услуги», «хочу сайт», «AI Bot», «защита данных».`;

/** /site hub — ownership first, project second. */
export const PUBLIC_SITE_WELCOME = `Здравствуйте! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.\n\nСайты (Basic / Business / Premium), AI Bot, анализ и ремонт. Данные не передаём третьим лицам.\n\nНапишите задачу — сразу дам ссылку на форму. Кнопка «Новый чат» сбрасывает диалог.`;

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
