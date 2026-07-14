/**
 * B-001 Guided Commerce — Mission 1 purchase path (session state).
 */

import { claimProjectFromMessage, mergeClaimDraft } from "./projectIdentity";

export type GuidedGoalId =
  | "get_clients"
  | "sell_online"
  | "accept_payments"
  | "automate"
  | "fix_problem"
  | "improve_site";

export type GuidedStep = "goal" | "company" | "logo" | "draft_ready" | "offer" | "pay" | "tune";

export type LogoChoice = "yes" | "no" | "auto" | null;

export type GuidedProductStage = "draft" | "owned";

export type GuidedCommerceState = {
  step: GuidedStep;
  goalId: GuidedGoalId | null;
  companyName: string;
  logoChoice: LogoChoice;
  brandHue: number | null;
  clientEmail: string;
  orderId: string | null;
  priceEur: number | null;
  priceLabel: string | null;
  /** Factory Product id — same object from preview through payment. */
  productId: string | null;
  productStage: GuidedProductStage;
};

export const GUIDED_SITE_INCLUDES = [
  "Дизайн под ваш бренд",
  "Мобильная версия",
  "Базовая SEO-структура",
  "Юридические страницы",
  "Продолжение работы с Vector",
] as const;

export const GUIDED_GOAL_WEBSITE_ID: GuidedGoalId = "sell_online";

export const GUIDED_GOALS: Array<{
  id: GuidedGoalId;
  emoji: string;
  label: string;
  available: boolean;
}> = [
  { id: "sell_online", emoji: "🌐", label: "Получить сайт", available: true },
  { id: "get_clients", emoji: "📈", label: "Получать клиентов", available: false },
  { id: "accept_payments", emoji: "💳", label: "Принимать оплату", available: false },
  { id: "automate", emoji: "⚙️", label: "Автоматизацию", available: false },
  { id: "fix_problem", emoji: "🔧", label: "Исправить проблему", available: false },
  { id: "improve_site", emoji: "📱", label: "Доработать проект", available: false },
];

export function isGuidedGoalAvailable(goalId: GuidedGoalId): boolean {
  return GUIDED_GOALS.find((g) => g.id === goalId)?.available ?? false;
}

export const GUIDED_PREVIEW_STEPS = [
  { id: "name", label: "Название" },
  { id: "colors", label: "Черновик" },
  { id: "logo", label: "Логотип" },
  { id: "contacts", label: "Контакты" },
] as const;

const STORAGE_KEY = "vc_guided_commerce_s4";

export const GUIDED_COMMERCE_EVENT = "genesis:guided-commerce";

const EMPTY: GuidedCommerceState = {
  step: "goal",
  goalId: null,
  companyName: "",
  logoChoice: null,
  brandHue: null,
  clientEmail: "",
  orderId: null,
  priceEur: null,
  priceLabel: null,
  productId: null,
  productStage: "draft",
};

function hashHue(text: string): number {
  let h = 0;
  for (let i = 0; i < text.length; i += 1) h = (h * 31 + text.charCodeAt(i)) % 360;
  return h;
}

function normalizeState(raw: Partial<GuidedCommerceState>): GuidedCommerceState {
  const merged = { ...EMPTY, ...raw };
  if (merged.companyName.trim() && merged.brandHue == null) {
    merged.brandHue = hashHue(merged.companyName.trim());
  }
  if (!merged.companyName.trim() && merged.step === "logo") {
    merged.step = "company";
  }
  if (!merged.logoChoice && (merged.step === "draft_ready" || merged.step === "offer" || merged.step === "pay")) {
    merged.step = merged.companyName.trim() ? "logo" : "company";
  }
  return merged;
}

export function loadGuidedCommerce(): GuidedCommerceState {
  if (typeof window === "undefined") return { ...EMPTY };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const legacy = sessionStorage.getItem("vc_guided_commerce_s1");
      if (legacy) return normalizeState(JSON.parse(legacy) as Partial<GuidedCommerceState>);
      return { ...EMPTY };
    }
    return normalizeState(JSON.parse(raw) as Partial<GuidedCommerceState>);
  } catch {
    return { ...EMPTY };
  }
}

export function saveGuidedCommerce(state: GuidedCommerceState): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent(GUIDED_COMMERCE_EVENT, { detail: state }));
}

export function resetGuidedCommerce(): GuidedCommerceState {
  const next = { ...EMPTY };
  saveGuidedCommerce(next);
  return next;
}

export function selectGuidedGoal(goalId: GuidedGoalId): GuidedCommerceState {
  if (!isGuidedGoalAvailable(goalId)) {
    return loadGuidedCommerce();
  }
  const next: GuidedCommerceState = {
    step: "company",
    goalId,
    companyName: "",
    logoChoice: null,
    brandHue: null,
    clientEmail: "",
    orderId: null,
    priceEur: null,
    priceLabel: null,
    productId: null,
    productStage: "draft",
  };
  saveGuidedCommerce(next);
  syncGoalToProjectDraft(goalId);
  return next;
}

export function submitCompanyNameAndAdvance(name: string): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const trimmed = name.trim();
  if (!trimmed) return prev;
  const nameChanged = prev.companyName.trim() !== trimmed;
  const next: GuidedCommerceState = {
    ...prev,
    companyName: trimmed,
    brandHue: hashHue(trimmed),
    step: "logo",
    logoChoice: null,
    productId: nameChanged ? null : prev.productId,
    productStage: "draft",
  };
  saveGuidedCommerce(next);
  syncCompanyToProjectDraft(trimmed, prev.goalId);
  return next;
}

export function setGuidedLogoChoice(choice: LogoChoice): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = {
    ...prev,
    logoChoice: choice,
    step: choice ? "draft_ready" : prev.step,
  };
  saveGuidedCommerce(next);
  return next;
}

export function advanceGuidedToOffer(priceEur: number, priceLabel: string | null): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = {
    ...prev,
    step: "offer",
    priceEur,
    priceLabel,
  };
  saveGuidedCommerce(next);
  return next;
}

export function advanceGuidedToTune(): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = { ...prev, step: "tune" };
  saveGuidedCommerce(next);
  return next;
}

export function setGuidedClientEmail(email: string): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = { ...prev, clientEmail: email.trim() };
  saveGuidedCommerce(next);
  return next;
}

export function advanceGuidedToPay(orderId: string, priceEur: number, priceLabel: string | null): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = {
    ...prev,
    step: "pay",
    orderId,
    priceEur,
    priceLabel,
  };
  saveGuidedCommerce(next);
  return next;
}

export function setGuidedProductId(productId: string): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  const next: GuidedCommerceState = {
    ...prev,
    productId: productId.trim() || null,
    productStage: "draft",
  };
  saveGuidedCommerce(next);
  return next;
}

export function markGuidedProductOwned(): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  if (!prev.productId) return prev;
  const next: GuidedCommerceState = { ...prev, productStage: "owned" };
  saveGuidedCommerce(next);
  return next;
}

function syncGoalToProjectDraft(goalId: GuidedGoalId): void {
  const label = GUIDED_GOALS.find((g) => g.id === goalId)?.label ?? goalId;
  claimProjectFromMessage(`Моя цель: ${label}`);
}

function syncCompanyToProjectDraft(name: string, goalId: GuidedGoalId | null): void {
  const goalLabel = goalId ? GUIDED_GOALS.find((g) => g.id === goalId)?.label : null;
  const text = goalLabel
    ? `Компания ${name}. Цель: ${goalLabel}`
    : `Компания ${name}`;
  mergeClaimDraft(text);
}

export function guidedPreviewPercent(state: GuidedCommerceState): number {
  let done = 0;
  if (state.goalId) done += 1;
  if (state.companyName.trim()) done += 1;
  if (state.productId) done += 2;
  if (state.logoChoice) done += 1;
  if (state.step === "offer" || state.step === "pay") done += 1;
  return Math.min(100, Math.round((done / 6) * 100));
}

export function previewStepStatus(
  stepId: (typeof GUIDED_PREVIEW_STEPS)[number]["id"],
  state: GuidedCommerceState,
): "done" | "active" | "pending" {
  const hasName = Boolean(state.companyName.trim());
  const hasLogo = Boolean(state.logoChoice);

  switch (stepId) {
    case "name":
      if (hasName) return "done";
      if (state.step === "company") return "active";
      return state.goalId ? "pending" : "pending";
    case "colors":
      if (state.productId) return "done";
      if (hasName) return "active";
      return "pending";
    case "logo":
      if (hasLogo) return "done";
      if (state.step === "logo") return "active";
      return "pending";
    case "contacts":
      if (state.step === "offer" || state.step === "pay") return "done";
      if (state.step === "draft_ready" && hasLogo) return "active";
      return "pending";
    default:
      return "pending";
  }
}

export function companyInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "VC";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}
