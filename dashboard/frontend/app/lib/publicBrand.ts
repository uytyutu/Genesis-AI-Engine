/** Public brand — Virtus Core · Vector (mirrors backend public_brand.py). */

export const BRAND_NAME = "Virtus Core";
export const ASSISTANT_NAME = "Vector";
export const BRAND_SIGNATURE = "by Virtus Core";
export const ASSISTANT_TAGLINE = "Digital Company";

export const STUDIO_NAME = "Virtus Studio";
export const CHAT_FEATURE = ASSISTANT_NAME;

type WelcomeLocale = "de" | "en" | "ru" | "uk" | string;

const WELCOME: Record<"de" | "en" | "ru" | "uk", string> = {
  de: `Guten Tag! Ich bin ${ASSISTANT_NAME} — Berater von ${BRAND_NAME}.

Ich kenne alle Produkte, die Sie hier kaufen können (Websites, AI Bot, Analyse). Beschreiben Sie Ihre Branche oder senden Sie einen Businessplan — ich empfehle das passende Paket. Im Chat baue ich keine Websites; danach führt der Link zur Anfrage.

In Ihrem Virtus-Core-Projekt bleibe ich als Vector bei Ihnen und steuere die gebuchten Rollen.`,
  en: `Hello! I'm ${ASSISTANT_NAME} — consultant at ${BRAND_NAME}.

I know every product you can buy here (websites, AI Bot, analysis). Describe your niche or share a business plan — I'll recommend the right package. I don't build sites in chat; next step is the order form.

Inside your Virtus Core project I stay with you as Vector and run the roles you purchased.`,
  ru: `Здравствуйте! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.

Знаю все продукты, которые можно купить здесь (сайты, AI Bot, анализ). Опишите нишу или пришлите бизнес-план — предложу пакет. Сайты в чате не собираю — дальше форма заявки.

В проекте Virtus Core я остаюсь с вами как Vector и веду купленные роли.`,
  uk: `Вітаю! Я ${ASSISTANT_NAME} — консультант ${BRAND_NAME}.

Знаю всі продукти, які можна купити тут. Опишіть нішу або надішліть бізнес-план — запропоную пакет.`,
};

/** @deprecated prefer publicWelcomeForLocale(uiLocale) */
export const PUBLIC_WELCOME = WELCOME.de;

/** /site hub — ownership first, project second. */
export const PUBLIC_SITE_WELCOME = WELCOME.de;

export function publicWelcomeForLocale(locale: WelcomeLocale): string {
  const base = String(locale || "de").split("-")[0].toLowerCase();
  if (base === "en" || base === "ru" || base === "uk" || base === "de") {
    return WELCOME[base];
  }
  return WELCOME.de;
}

export type VectorFaqItem = { label: string; message: string };

/** Frequent questions for storefront Vector chat. */
export function vectorFaqForLocale(locale: WelcomeLocale): VectorFaqItem[] {
  const base = String(locale || "de").split("-")[0].toLowerCase();
  if (base === "en") {
    return [
      { label: "Packages", message: "What's the difference between Basic, Business and Premium?" },
      { label: "My niche", message: "Which package fits my industry? I'll describe it." },
      { label: "Business plan", message: "Please analyze my business plan and recommend a package." },
      { label: "AI Bot", message: "Do I need an AI Bot for my business?" },
      { label: "Privacy", message: "How do you protect my data?" },
    ];
  }
  if (base === "ru") {
    return [
      { label: "Пакеты", message: "Чем отличаются Basic, Business и Premium?" },
      { label: "Ниша", message: "Какой пакет подходит под мою нишу? Опишу её." },
      { label: "Бизнес-план", message: "Проанализируй бизнес-план и предложи пакет." },
      { label: "AI Bot", message: "Нужен ли мне AI Bot для бизнеса?" },
      { label: "Данные", message: "Как вы защищаете мои данные?" },
    ];
  }
  if (base === "uk") {
    return [
      { label: "Пакети", message: "Чим відрізняються Basic, Business і Premium?" },
      { label: "Ніша", message: "Який пакет під мою нішу?" },
      { label: "Бізнес-план", message: "Проаналізуй бізнес-план і запропонуй пакет." },
      { label: "AI Bot", message: "Чи потрібен мені AI Bot?" },
      { label: "Дані", message: "Як захищаєте мої дані?" },
    ];
  }
  return [
    { label: "Pakete", message: "Was ist der Unterschied zwischen Basic, Business und Premium?" },
    { label: "Branche", message: "Welches Paket passt zu meiner Branche? Ich beschreibe sie." },
    { label: "Businessplan", message: "Bitte analysieren Sie meinen Businessplan und empfehlen Sie ein Paket." },
    { label: "AI Bot", message: "Brauche ich einen AI Bot für mein Business?" },
    { label: "Datenschutz", message: "Wie schützt ihr meine Daten?" },
  ];
}

export function publicLeadCaptureWelcome(nicheLabel: string): string {
  return (
    `Guten Tag! Ich bin ${ASSISTANT_NAME}.\n\n` +
    `Beschreiben Sie das Problem — ich erstelle die Anfrage für ${nicheLabel}. ` +
    `Ort, Dringlichkeit und Kontakt können in einer Nachricht stehen.`
  );
}

export function brandSignatureLines(includeTagline = false): string[] {
  if (includeTagline) {
    return [ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE];
  }
  return [ASSISTANT_NAME, BRAND_SIGNATURE];
}
