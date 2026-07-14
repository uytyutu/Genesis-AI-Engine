/**
 * Dialog engine — guided journey from conversation context, not form steps.
 */

import {
  loadGuidedCommerce,
  saveGuidedCommerce,
  type GuidedCommerceState,
  type LogoChoice,
} from "./guidedCommerce";
import { extractClaimFactsFromMessage } from "./projectIdentity";

export type DialogFacts = {
  companyName?: string | null;
  businessActivity?: string | null;
  siteVision?: string | null;
  audience?: string | null;
  clientEmail?: string | null;
  clientPhone?: string | null;
  clientCity?: string | null;
  logoChoice?: LogoChoice | null;
};

export type DialogGap = "company" | "activity" | "vision" | "email" | "audience" | "logo";

const EMAIL_RE = /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i;
const PHONE_RE = /(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}(?:[\s-]?\d{2,4})?/;

const FOLLOW_UP: Record<DialogGap, string> = {
  company: "Как называется ваша компания или бренд?",
  activity: "Расскажите коротко, чем вы занимаетесь — я подстрою тексты под ваш бизнес.",
  vision: "Что должен сделать посетитель на сайте — записаться, позвонить, оставить заявку?",
  audience: "Для какой аудитории вы хотите этот сайт?",
  email: "На какой email прислать подтверждение и доступ к проекту?",
  logo: "Есть ли у вас логотип — или собрать его из названия?",
};

function cleanSentence(text: string, max = 160): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max - 1)}…`;
}

function extractBusinessActivity(text: string, industry: string | null): string | null {
  const t = text.trim();
  const m =
    t.match(/(?:занимаемся|мы\s+делаем|предлагаем|услуг[аи]|бизнес[:\s-]+)([^.!\n]{8,120})/i) ||
    t.match(/(?:ich\s+bin|wir\s+sind|we\s+are|we\s+offer)\s+([^.\n]{8,120})/i);
  if (m?.[1]) return cleanSentence(m[1]);
  if (industry && t.length > 24) return cleanSentence(`${industry}. ${t}`);
  if (industry) return industry;
  if (t.length > 32 && /(сайт|бизнес|компани|клиент|услуг)/i.test(t)) return cleanSentence(t);
  return null;
}

function extractSiteVision(text: string, goal: string | null): string | null {
  const t = text.trim();
  if (/(запис|termin|book|appointment)/i.test(t)) return "Запись на приём или услугу";
  if (/(позвон|звон|anruf|call)/i.test(t)) return "Позвонить или связаться";
  if (/(заявк|форма|контакт|написать)/i.test(t)) return "Оставить заявку";
  if (/(купи|заказ|shop|buy)/i.test(t)) return "Оформить заказ или покупку";
  if (goal) return goal;
  if (/(хочу|нужен|нужно).{0,40}(сайт|лендинг)/i.test(t)) return "Понятный сайт с действием для посетителя";
  return null;
}

function extractAudience(text: string): string | null {
  const m =
    text.match(/(?:для\s+(?:кого|какой\s+аудитории?))[\s,:-]+([^.\n!?]{4,80})/i) ||
    text.match(/(?:аудитория|клиенты|zielgruppe)[\s,:-]+([^.\n!?]{4,80})/i);
  return m?.[1] ? cleanSentence(m[1], 80) : null;
}

function extractLogoChoice(text: string): LogoChoice | null {
  if (/(нет|без|не\s+имею).{0,24}логотип/i.test(text)) return "no";
  if (/(есть|имею|загружу|свой).{0,24}логотип/i.test(text)) return "yes";
  if (/(создай|сделай|собери|авто).{0,24}логотип/i.test(text)) return "auto";
  return null;
}

export function extractDialogFacts(message: string): DialogFacts {
  const text = (message || "").trim();
  if (!text) return {};

  const claim = extractClaimFactsFromMessage(text);
  const email = text.match(EMAIL_RE)?.[0] ?? null;
  const phone = text.match(PHONE_RE)?.[0] ?? null;

  return {
    companyName: claim.companyName,
    businessActivity: extractBusinessActivity(text, claim.industry ?? null),
    siteVision: extractSiteVision(text, claim.goal ?? null),
    audience: extractAudience(text),
    clientEmail: email,
    clientPhone: phone,
    clientCity: claim.location,
    logoChoice: extractLogoChoice(text),
  };
}

function mergeFact<T extends string>(prev: string, next: string | null | undefined): string {
  const n = (next ?? "").trim();
  if (!n) return prev;
  if (!prev.trim()) return n;
  if (prev.includes(n) || n.includes(prev)) return prev.length >= n.length ? prev : n;
  return `${prev.trim()}. ${n}`;
}

export function applyDialogFacts(facts: DialogFacts): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const companyChanged = Boolean(facts.companyName?.trim() && facts.companyName.trim() !== prev.companyName.trim());

  const next: GuidedCommerceState = {
    ...prev,
    companyName: facts.companyName?.trim() || prev.companyName,
    businessActivity: mergeFact(prev.businessActivity, facts.businessActivity),
    siteVision: mergeFact(prev.siteVision, facts.siteVision),
    clientCity: facts.clientCity?.trim() || prev.clientCity,
    clientPhone: facts.clientPhone?.trim() || prev.clientPhone,
    clientEmail: facts.clientEmail?.trim() || prev.clientEmail,
    draftReviewed: companyChanged ? false : prev.draftReviewed,
    productId: companyChanged ? null : prev.productId,
    logoChoice: facts.logoChoice ?? prev.logoChoice,
  };

  if (facts.audience?.trim()) {
    const aud = facts.audience.trim();
    if (!next.siteVision.includes(aud)) {
      next.siteVision = mergeFact(next.siteVision, `Аудитория: ${aud}`);
    }
  }

  if (facts.logoChoice && facts.logoChoice !== prev.logoChoice) {
    next.draftReviewed = false;
    next.productId = null;
  }

  next.step = resolveDialogStep(next);
  saveGuidedCommerce(next);
  return next;
}

export function ingestGuidedDialogMessage(message: string): GuidedCommerceState {
  return applyDialogFacts(extractDialogFacts(message));
}

export function dialogGaps(state: GuidedCommerceState): DialogGap[] {
  const gaps: DialogGap[] = [];
  if (!state.companyName.trim()) gaps.push("company");
  if (!state.businessActivity.trim()) gaps.push("activity");
  if (!state.siteVision.trim()) gaps.push("vision");
  if (
    state.businessActivity.trim() &&
    state.siteVision.trim() &&
    !/аудитор|для\s+\w|клиент/i.test(state.siteVision) &&
    state.siteVision.length < 48
  ) {
    gaps.push("audience");
  }
  if (!state.clientEmail.trim()) gaps.push("email");
  if (!state.logoChoice) gaps.push("logo");
  return gaps;
}

export function pickDialogFollowUp(state: GuidedCommerceState): string | null {
  const gaps = dialogGaps(state);
  if (!gaps.length) return null;
  return FOLLOW_UP[gaps[0]];
}

export function isDialogReadyForDraft(state: GuidedCommerceState): boolean {
  return Boolean(
    state.goalId &&
      state.companyName.trim() &&
      state.businessActivity.trim() &&
      state.siteVision.trim() &&
      state.clientEmail.trim() &&
      state.logoChoice,
  );
}

export function resolveDialogStep(state: GuidedCommerceState): GuidedCommerceState["step"] {
  if (state.step === "pay" || state.step === "offer") return state.step;
  if (state.draftReviewed && state.productId) return "offer";
  if (state.productId && state.logoChoice) return "review";
  if (isDialogReadyForDraft(state)) return "review";
  return "discover";
}

export function assistantAlreadyClarifies(answer: string): boolean {
  return /[?？]/.test(answer) || /(уточн|расскаж|как\s+называ|чем\s+занима|email|логотип|аудитор)/i.test(answer);
}

export function enrichAnswerWithDialogFollowUp(answer: string, state: GuidedCommerceState): string {
  if (state.step === "offer" || state.step === "pay") return answer;
  const followUp = pickDialogFollowUp(state);
  if (!followUp || assistantAlreadyClarifies(answer)) return answer;
  const trimmed = answer.trim();
  if (!trimmed) return followUp;
  return `${trimmed}\n\n${followUp}`;
}

export function buildGuidedJourneyContext(state: GuidedCommerceState) {
  return {
    mode: "dialog",
    known: {
      company: state.companyName || null,
      activity: state.businessActivity || null,
      vision: state.siteVision || null,
      email: state.clientEmail || null,
      city: state.clientCity || null,
      phone: state.clientPhone || null,
      logo: state.logoChoice,
    },
    missing: dialogGaps(state),
    follow_up: pickDialogFollowUp(state),
  };
}
