/** Viral share-loops — each creates a reason to send a link. */

import { t, type Locale } from "@/lib/i18n/dictionaries";

export type ViralKind =
  | "think"
  | "map"
  | "guess"
  | "say"
  | "when"
  | "words"
  | "duo"
  | "fragment"
  | "ask";

export type ViralSku =
  | "VIRAL_THINK"
  | "VIRAL_THINK_MAP"
  | "VIRAL_MAP"
  | "VIRAL_GUESS_HINT"
  | "VIRAL_GUESS_REVEAL"
  | "VIRAL_SAY"
  | "VIRAL_WHEN"
  | "VIRAL_WORDS"
  | "VIRAL_WORDS_UNLOCK"
  | "VIRAL_DUO"
  | "VIRAL_FRAGMENT"
  | "VIRAL_ASK";

export type ViralProduct = {
  sku: ViralSku;
  kind: ViralKind;
  emoji: string;
  titleKey: string;
  subtitleKey: string;
  /** EUR cents — 0 = free to create / answer */
  amountCents: number;
  createFree: boolean;
};

export const VIRAL_PRODUCTS: Record<ViralSku, ViralProduct> = {
  VIRAL_THINK: {
    sku: "VIRAL_THINK",
    kind: "think",
    emoji: "🔮",
    titleKey: "viral.hub.think.title",
    subtitleKey: "viral.prod.think.subtitle",
    amountCents: 0,
    createFree: true,
  },
  VIRAL_THINK_MAP: {
    sku: "VIRAL_THINK_MAP",
    kind: "think",
    emoji: "🗺️",
    titleKey: "viral.prod.thinkMap.title",
    subtitleKey: "viral.prod.thinkMap.subtitle",
    amountCents: 299,
    createFree: false,
  },
  VIRAL_MAP: {
    sku: "VIRAL_MAP",
    kind: "map",
    emoji: "🧬",
    titleKey: "viral.hub.map.title",
    subtitleKey: "viral.prod.map.subtitle",
    amountCents: 199,
    createFree: false,
  },
  VIRAL_GUESS_HINT: {
    sku: "VIRAL_GUESS_HINT",
    kind: "guess",
    emoji: "💡",
    titleKey: "viral.prod.guessHint.title",
    subtitleKey: "viral.prod.guessHint.subtitle",
    amountCents: 99,
    createFree: false,
  },
  VIRAL_GUESS_REVEAL: {
    sku: "VIRAL_GUESS_REVEAL",
    kind: "guess",
    emoji: "👀",
    titleKey: "viral.prod.guessReveal.title",
    subtitleKey: "viral.prod.guessReveal.subtitle",
    amountCents: 99,
    createFree: false,
  },
  VIRAL_SAY: {
    sku: "VIRAL_SAY",
    kind: "say",
    emoji: "🔥",
    titleKey: "viral.hub.say.title",
    subtitleKey: "viral.prod.say.subtitle",
    amountCents: 199,
    createFree: false,
  },
  VIRAL_WHEN: {
    sku: "VIRAL_WHEN",
    kind: "when",
    emoji: "⏳",
    titleKey: "viral.hub.when.title",
    subtitleKey: "viral.prod.when.subtitle",
    amountCents: 249,
    createFree: false,
  },
  VIRAL_WORDS: {
    sku: "VIRAL_WORDS",
    kind: "words",
    emoji: "🎭",
    titleKey: "viral.hub.words.title",
    subtitleKey: "viral.prod.words.subtitle",
    amountCents: 0,
    createFree: true,
  },
  VIRAL_WORDS_UNLOCK: {
    sku: "VIRAL_WORDS_UNLOCK",
    kind: "words",
    emoji: "✨",
    titleKey: "viral.prod.wordsUnlock.title",
    subtitleKey: "viral.prod.wordsUnlock.subtitle",
    amountCents: 199,
    createFree: false,
  },
  VIRAL_DUO: {
    sku: "VIRAL_DUO",
    kind: "duo",
    emoji: "🪞",
    titleKey: "viral.hub.duo.title",
    subtitleKey: "viral.prod.duo.subtitle",
    amountCents: 249,
    createFree: false,
  },
  VIRAL_FRAGMENT: {
    sku: "VIRAL_FRAGMENT",
    kind: "fragment",
    emoji: "📦",
    titleKey: "viral.hub.fragment.title",
    subtitleKey: "viral.prod.fragment.subtitle",
    amountCents: 0,
    createFree: true,
  },
  VIRAL_ASK: {
    sku: "VIRAL_ASK",
    kind: "ask",
    emoji: "🧠",
    titleKey: "viral.hub.ask.title",
    subtitleKey: "viral.prod.ask.subtitle",
    amountCents: 0,
    createFree: true,
  },
};

export const LOOP_HUB: Array<{
  kind: ViralKind;
  sku: ViralSku;
  emoji: string;
  titleKey: string;
  blurbKey: string;
  priceLabelKey: string;
  /** Live on loops hub — guess works via Secrets redirect */
  live: boolean;
}> = [
  {
    kind: "think",
    sku: "VIRAL_THINK",
    emoji: "🔮",
    titleKey: "viral.hub.think.title",
    blurbKey: "viral.hub.think.blurb",
    priceLabelKey: "viral.hub.think.price",
    live: true,
  },
  {
    kind: "map",
    sku: "VIRAL_MAP",
    emoji: "🧬",
    titleKey: "viral.hub.map.title",
    blurbKey: "viral.hub.map.blurb",
    priceLabelKey: "viral.hub.map.price",
    live: true,
  },
  {
    kind: "guess",
    sku: "VIRAL_GUESS_HINT",
    emoji: "👀",
    titleKey: "viral.hub.guess.title",
    blurbKey: "viral.hub.guess.blurb",
    priceLabelKey: "viral.hub.guess.price",
    live: true,
  },
  {
    kind: "say",
    sku: "VIRAL_SAY",
    emoji: "🔥",
    titleKey: "viral.hub.say.title",
    blurbKey: "viral.hub.say.blurb",
    priceLabelKey: "viral.hub.say.price",
    live: true,
  },
  {
    kind: "when",
    sku: "VIRAL_WHEN",
    emoji: "⏳",
    titleKey: "viral.hub.when.title",
    blurbKey: "viral.hub.when.blurb",
    priceLabelKey: "viral.hub.when.price",
    live: true,
  },
  {
    kind: "words",
    sku: "VIRAL_WORDS",
    emoji: "🎭",
    titleKey: "viral.hub.words.title",
    blurbKey: "viral.hub.words.blurb",
    priceLabelKey: "viral.hub.words.price",
    live: true,
  },
  {
    kind: "duo",
    sku: "VIRAL_DUO",
    emoji: "🪞",
    titleKey: "viral.hub.duo.title",
    blurbKey: "viral.hub.duo.blurb",
    priceLabelKey: "viral.hub.duo.price",
    live: true,
  },
  {
    kind: "fragment",
    sku: "VIRAL_FRAGMENT",
    emoji: "📦",
    titleKey: "viral.hub.fragment.title",
    blurbKey: "viral.hub.fragment.blurb",
    priceLabelKey: "viral.hub.fragment.price",
    live: true,
  },
  {
    kind: "ask",
    sku: "VIRAL_ASK",
    emoji: "🧠",
    titleKey: "viral.hub.ask.title",
    blurbKey: "viral.hub.ask.blurb",
    priceLabelKey: "viral.hub.ask.price",
    live: true,
  },
];

export const THINK_QUESTIONS = [
  "What kind of person am I?",
  "What do you like about me?",
  "What am I doing wrong?",
  "What have you never told me?",
  "Who do you think I’ll be in 5 years?",
];

export const MAP_QUESTIONS = [
  "Would you leave first — or stay until the end?",
  "Money or freedom?",
  "What would you never forgive?",
  "Which childhood moment do you remember most?",
  "Quiet night in or spontaneous adventure?",
  "Say it now — or wait forever?",
  "Protect yourself — or protect others first?",
  "What are you most afraid people see in you?",
];

export const DUO_QUESTIONS = [
  "Who of you moves to another country first?",
  "What matters more to them — honesty or kindness?",
  "Who apologizes first after a fight?",
  "What gift would make them cry happy tears?",
  "Where will you both be in 10 years?",
];

export const SAY_INTENTS = [
  { id: "miss", labelKey: "viral.sayIntent.miss" },
  { id: "proud", labelKey: "viral.sayIntent.proud" },
  { id: "mad", labelKey: "viral.sayIntent.mad" },
  { id: "thanks", labelKey: "viral.sayIntent.thanks" },
  { id: "scared", labelKey: "viral.sayIntent.scared" },
  { id: "sorry", labelKey: "viral.sayIntent.sorry" },
  { id: "never", labelKey: "viral.sayIntent.never" },
] as const;

export const WHEN_TRIGGERS = [
  { id: "age_18", labelKey: "viral.whenTrigger.age_18" },
  { id: "first_job", labelKey: "viral.whenTrigger.first_job" },
  { id: "low", labelKey: "viral.whenTrigger.low" },
  { id: "one_year", labelKey: "viral.whenTrigger.one_year" },
  { id: "birthday", labelKey: "viral.whenTrigger.birthday" },
  { id: "love", labelKey: "viral.whenTrigger.love" },
  { id: "miss_me", labelKey: "viral.whenTrigger.miss_me" },
  { id: "need_it", labelKey: "viral.whenTrigger.need_it" },
] as const;

export function viralProductTitle(sku: ViralSku, locale: Locale = "en"): string {
  return t(locale, VIRAL_PRODUCTS[sku].titleKey);
}

export function shortCode(): string {
  const alphabet = "abcdefghijkmnopqrstuvwxyz23456789";
  let out = "";
  for (let i = 0; i < 8; i++) out += alphabet[Math.floor(Math.random() * alphabet.length)];
  return out;
}

export function isViralKind(v: string): v is ViralKind {
  return ["think", "map", "guess", "say", "when", "words", "duo", "fragment", "ask"].includes(v);
}
