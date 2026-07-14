/**
 * Product sales journey — what we ask before draft + payment.
 */

import type { GuidedCommerceState } from "./guidedCommerce";
import { isDialogReadyForDraft } from "./guidedDialogEngine";

export function isGuidedBriefComplete(state: GuidedCommerceState): boolean {
  return isDialogReadyForDraft(state);
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
