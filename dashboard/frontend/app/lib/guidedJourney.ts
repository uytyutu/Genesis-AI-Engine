/**
 * Product sales journey — what we ask before draft + payment.
 */

import type { GuidedCommerceState, GuidedStep } from "./guidedCommerce";

export const JOURNEY_STEP_HINTS: Record<
  Exclude<GuidedStep, "goal" | "pay" | "tune">,
  { title: string; why: string }
> = {
  company: {
    title: "Как называется компания?",
    why: "Название — основа бренда на сайте и в черновике.",
  },
  activity: {
    title: "Чем вы занимаетесь?",
    why: "Vector подберёт тексты и структуру под ваш реальный бизнес — не шаблон.",
  },
  vision: {
    title: "Что должен сделать посетитель на сайте?",
    why: "Запись, звонок, покупка — от этого зависит кнопка и смысл страницы.",
  },
  contacts: {
    title: "Как клиенты свяжутся с вами?",
    why: "Контакты попадут в черновик и в заказ — без сюрпризов после оплаты.",
  },
  logo: {
    title: "Есть логотип?",
    why: "Можно добавить свой, создать из названия или оставить на потом.",
  },
  review: {
    title: "Это то, что вы хотели?",
    why: "Оплата — только когда черновик справа отражает ваши ответы.",
  },
  offer: {
    title: "Права на ваш черновик",
    why: "Вы покупаете именно тот сайт, который видите — без пересборки.",
  },
  draft_ready: {
    title: "Проверьте черновик",
    why: "Сверьте тексты и структуру с тем, что рассказали Vector.",
  },
};

export function isGuidedBriefComplete(state: GuidedCommerceState): boolean {
  return Boolean(
    state.goalId &&
      state.companyName.trim() &&
      state.businessActivity.trim() &&
      state.siteVision.trim() &&
      state.clientEmail.trim() &&
      state.logoChoice,
  );
}

export function buildGuidedSalesBrief(state: GuidedCommerceState): string {
  const name = state.companyName.trim();
  const activity = state.businessActivity.trim();
  const vision = state.siteVision.trim();
  const city = state.clientCity.trim();
  const phone = state.clientPhone.trim();
  const logo =
    state.logoChoice === "yes"
      ? "Client has logo"
      : state.logoChoice === "auto"
        ? "Generate logo from business name"
        : state.logoChoice === "no"
          ? "No logo yet"
          : "";

  const parts = [
    `Website for ${name}.`,
    `Business: ${activity}`,
    `Visitor goal: ${vision}`,
  ];
  if (city) parts.push(`City: ${city}.`);
  if (phone) parts.push(`Phone: ${phone}.`);
  if (logo) parts.push(logo);
  return parts.join(" ");
}

export function guidedReviewSummary(state: GuidedCommerceState): string[] {
  const lines: string[] = [];
  if (state.companyName.trim()) lines.push(`Компания: ${state.companyName.trim()}`);
  if (state.businessActivity.trim()) lines.push(`Деятельность: ${state.businessActivity.trim()}`);
  if (state.siteVision.trim()) lines.push(`Цель сайта: ${state.siteVision.trim()}`);
  if (state.clientCity.trim()) lines.push(`Город: ${state.clientCity.trim()}`);
  if (state.clientPhone.trim()) lines.push(`Телефон: ${state.clientPhone.trim()}`);
  if (state.clientEmail.trim()) lines.push(`Email: ${state.clientEmail.trim()}`);
  return lines;
}
