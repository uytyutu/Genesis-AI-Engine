/** Configurable microtransaction catalog — amounts snapshotted on order. */

export type GiftSku =
  | "SEND_MOMENT"
  | "SEND_JOKE"
  | "SEND_SURPRISE"
  | "SEND_ANON"
  | "SEND_OPEN_WHEN"
  | "SEND_TIME_CAPSULE"
  | "SEND_STORY"
  | "SEND_QUESTION"
  | "SEND_BIG_MOMENT"
  | "SEND_REVEAL"
  | "SEND_DROP"
  | "SEND_SECRET"
  | "ASK_HINT"
  | "ASK_REVEAL"
  | "PACK_PARTY"
  | "PACK_EVENT"
  | "PACK_AI_PARTY"
  | "PACK_SMART_BOTS"
  | "PACK_ANON_PLUS"
  | "VIRAL_THINK_MAP"
  | "VIRAL_MAP"
  | "VIRAL_SAY"
  | "VIRAL_WHEN"
  | "VIRAL_WORDS_UNLOCK"
  | "VIRAL_DUO";

export type GiftPillar = "send" | "anon" | "open_when" | "drop" | "pack" | "engage" | "viral";

export const DROP_MOODS = [
  "sweet",
  "funny",
  "suspicious",
  "savage",
  "secret",
  "beautiful",
  "unexpected",
] as const;

export type DropMood = (typeof DROP_MOODS)[number];

export interface ProductDef {
  sku: GiftSku;
  pillar: GiftPillar;
  emoji: string;
  nameKey: string;
  descKey: string;
  /** EUR cents */
  amountCents: number;
  currency: "eur";
  impulse: "impulse" | "small" | "emotional" | "story" | "premium" | "event";
}

export const PRODUCTS: Record<GiftSku, ProductDef> = {
  SEND_SECRET: {
    sku: "SEND_SECRET",
    pillar: "anon",
    emoji: "🔐",
    nameKey: "products.secret.name",
    descKey: "products.secret.desc",
    amountCents: 0,
    currency: "eur",
    impulse: "impulse",
  },
  ASK_HINT: {
    sku: "ASK_HINT",
    pillar: "engage",
    emoji: "💡",
    nameKey: "products.askHint.name",
    descKey: "products.askHint.desc",
    amountCents: 99,
    currency: "eur",
    impulse: "impulse",
  },
  ASK_REVEAL: {
    sku: "ASK_REVEAL",
    pillar: "engage",
    emoji: "👀",
    nameKey: "products.askReveal.name",
    descKey: "products.askReveal.desc",
    amountCents: 99,
    currency: "eur",
    impulse: "impulse",
  },
  SEND_DROP: {
    sku: "SEND_DROP",
    pillar: "drop",
    emoji: "🔥",
    nameKey: "products.drop.name",
    descKey: "products.drop.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "impulse",
  },
  SEND_MOMENT: {
    sku: "SEND_MOMENT",
    pillar: "send",
    emoji: "💌",
    nameKey: "products.moment.name",
    descKey: "products.moment.desc",
    amountCents: 99,
    currency: "eur",
    impulse: "impulse",
  },
  SEND_JOKE: {
    sku: "SEND_JOKE",
    pillar: "send",
    emoji: "😂",
    nameKey: "products.joke.name",
    descKey: "products.joke.desc",
    amountCents: 99,
    currency: "eur",
    impulse: "impulse",
  },
  SEND_SURPRISE: {
    sku: "SEND_SURPRISE",
    pillar: "send",
    emoji: "🎁",
    nameKey: "products.surprise.name",
    descKey: "products.surprise.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "small",
  },
  SEND_ANON: {
    sku: "SEND_ANON",
    pillar: "anon",
    emoji: "🕵️",
    nameKey: "products.anon.name",
    descKey: "products.anon.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "small",
  },
  SEND_OPEN_WHEN: {
    sku: "SEND_OPEN_WHEN",
    pillar: "open_when",
    emoji: "🔒",
    nameKey: "products.openWhen.name",
    descKey: "products.openWhen.desc",
    amountCents: 249,
    currency: "eur",
    impulse: "emotional",
  },
  SEND_TIME_CAPSULE: {
    sku: "SEND_TIME_CAPSULE",
    pillar: "open_when",
    emoji: "⏳",
    nameKey: "products.timeCapsule.name",
    descKey: "products.timeCapsule.desc",
    amountCents: 299,
    currency: "eur",
    impulse: "emotional",
  },
  SEND_STORY: {
    sku: "SEND_STORY",
    pillar: "send",
    emoji: "❤️",
    nameKey: "products.story.name",
    descKey: "products.story.desc",
    amountCents: 499,
    currency: "eur",
    impulse: "story",
  },
  SEND_QUESTION: {
    sku: "SEND_QUESTION",
    pillar: "send",
    emoji: "❓",
    nameKey: "products.question.name",
    descKey: "products.question.desc",
    amountCents: 149,
    currency: "eur",
    impulse: "impulse",
  },
  SEND_BIG_MOMENT: {
    sku: "SEND_BIG_MOMENT",
    pillar: "send",
    emoji: "💎",
    nameKey: "products.bigMoment.name",
    descKey: "products.bigMoment.desc",
    amountCents: 999,
    currency: "eur",
    impulse: "premium",
  },
  SEND_REVEAL: {
    sku: "SEND_REVEAL",
    pillar: "anon",
    emoji: "🔓",
    nameKey: "products.reveal.name",
    descKey: "products.reveal.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "small",
  },
  PACK_PARTY: {
    sku: "PACK_PARTY",
    pillar: "pack",
    emoji: "🎪",
    nameKey: "products.party.name",
    descKey: "products.party.desc",
    amountCents: 999,
    currency: "eur",
    impulse: "premium",
  },
  PACK_EVENT: {
    sku: "PACK_EVENT",
    pillar: "pack",
    emoji: "🎉",
    nameKey: "products.event.name",
    descKey: "products.event.desc",
    amountCents: 4999,
    currency: "eur",
    impulse: "event",
  },
  PACK_AI_PARTY: {
    sku: "PACK_AI_PARTY",
    pillar: "pack",
    emoji: "🤖",
    nameKey: "products.aiParty.name",
    descKey: "products.aiParty.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "impulse",
  },
  PACK_SMART_BOTS: {
    sku: "PACK_SMART_BOTS",
    pillar: "pack",
    emoji: "🧠",
    nameKey: "products.smartBots.name",
    descKey: "products.smartBots.desc",
    amountCents: 299,
    currency: "eur",
    impulse: "small",
  },
  PACK_ANON_PLUS: {
    sku: "PACK_ANON_PLUS",
    pillar: "pack",
    emoji: "✨",
    nameKey: "products.anonPlus.name",
    descKey: "products.anonPlus.desc",
    amountCents: 499,
    currency: "eur",
    impulse: "premium",
  },
  VIRAL_THINK_MAP: {
    sku: "VIRAL_THINK_MAP",
    pillar: "viral",
    emoji: "🗺️",
    nameKey: "products.thinkMap.name",
    descKey: "products.thinkMap.desc",
    amountCents: 299,
    currency: "eur",
    impulse: "small",
  },
  VIRAL_MAP: {
    sku: "VIRAL_MAP",
    pillar: "viral",
    emoji: "🧬",
    nameKey: "products.viralMap.name",
    descKey: "products.viralMap.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "impulse",
  },
  VIRAL_SAY: {
    sku: "VIRAL_SAY",
    pillar: "viral",
    emoji: "🔥",
    nameKey: "products.viralSay.name",
    descKey: "products.viralSay.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "impulse",
  },
  VIRAL_WHEN: {
    sku: "VIRAL_WHEN",
    pillar: "viral",
    emoji: "⏳",
    nameKey: "products.viralWhen.name",
    descKey: "products.viralWhen.desc",
    amountCents: 249,
    currency: "eur",
    impulse: "emotional",
  },
  VIRAL_WORDS_UNLOCK: {
    sku: "VIRAL_WORDS_UNLOCK",
    pillar: "viral",
    emoji: "🎭",
    nameKey: "products.viralWords.name",
    descKey: "products.viralWords.desc",
    amountCents: 199,
    currency: "eur",
    impulse: "impulse",
  },
  VIRAL_DUO: {
    sku: "VIRAL_DUO",
    pillar: "viral",
    emoji: "🪞",
    nameKey: "products.viralDuo.name",
    descKey: "products.viralDuo.desc",
    amountCents: 249,
    currency: "eur",
    impulse: "emotional",
  },
};

export const PACK_SKUS: GiftSku[] = [
  "PACK_AI_PARTY",
  "PACK_SMART_BOTS",
  "PACK_ANON_PLUS",
  "PACK_PARTY",
  "PACK_EVENT",
];

export function isPackSku(sku: string): boolean {
  return PACK_SKUS.includes(sku as GiftSku);
}

export const THEMES = [
  "dream",
  "love",
  "funny",
  "mystery",
  "night",
  "magic",
  "birthday",
  "happy",
] as const;

export type ThemeId = (typeof THEMES)[number];

export const OPEN_WHEN_PRESETS = [
  "miss_you",
  "sad",
  "laugh",
  "before_sleep",
  "birthday",
  "after_fight",
  "motivation",
  "remember_me",
  "age_18",
  "first_job",
  "one_year",
  "find_love",
  "need_it",
] as const;

export function formatMoney(cents: number, currency = "eur", locale = "en"): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency.toUpperCase(),
  }).format(cents / 100);
}

export function getProduct(sku: string): ProductDef | null {
  return PRODUCTS[sku as GiftSku] ?? null;
}
