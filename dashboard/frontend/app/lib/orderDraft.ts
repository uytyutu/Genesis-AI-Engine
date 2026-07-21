/**
 * Mission 3A / A1.1 — Order Experience draft (localStorage).
 * Persist /order wizard progress so refresh does not lose the funnel.
 */

import { getVisitorId } from "./visitorId";

export const ORDER_DRAFT_VERSION = 1 as const;
const STORAGE_PREFIX = "vc_order_draft_v1";

export type OrderDraftMaterial = {
  id: string;
  filename: string;
  size: number;
  status_de: string;
  findings: { label_de?: string }[];
};

export type OrderDraftPayload = {
  v: typeof ORDER_DRAFT_VERSION;
  savedAt: number;
  formStep: number;
  packageId: string;
  manualPackage: boolean;
  brandStyle: string;
  businessName: string;
  description: string;
  companyWebsite: string;
  city: string;
  phone: string;
  whatsapp: string;
  email: string;
  needsLogo: boolean;
  needsDomain: boolean;
  domainStatus: "none" | "have_domain" | "need_help";
  existingDomain: string;
  googleBusiness: string;
  instagram: string;
  facebook: string;
  tiktok: string;
  linkedin: string;
  youtube: string;
  telegram: string;
  extraWishes: string;
  niche: string;
  specialization: string;
  serviceList: string;
  legalOwner: string;
  legalForm: string;
  legalStreet: string;
  legalZip: string;
  legalCity: string;
  legalDirector: string;
  legalVat: string;
  legalMaps: boolean;
  legalAnalytics: boolean;
  materials: OrderDraftMaterial[];
  purchaseType: "one_time" | "subscription";
};

export function orderDraftStorageKey(marketCode: string, visitorId?: string | null): string {
  const market = (marketCode || "DE").trim().toUpperCase() || "DE";
  const vid = (visitorId || "").trim() || getVisitorId("public");
  return `${STORAGE_PREFIX}:${market}:${vid}`;
}

export function isMeaningfulOrderDraft(draft: OrderDraftPayload | null | undefined): boolean {
  if (!draft || draft.v !== ORDER_DRAFT_VERSION) return false;
  if (draft.formStep > 1) return true;
  if ((draft.businessName || "").trim().length > 0) return true;
  if ((draft.email || "").trim().length > 0) return true;
  if ((draft.description || "").trim().length >= 8) return true;
  if ((draft.materials || []).length > 0) return true;
  return false;
}

export function loadOrderDraft(
  marketCode: string,
  visitorId?: string | null,
): OrderDraftPayload | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(orderDraftStorageKey(marketCode, visitorId));
    if (!raw) return null;
    const data = JSON.parse(raw) as OrderDraftPayload;
    if (!data || data.v !== ORDER_DRAFT_VERSION) return null;
    if (typeof data.formStep !== "number") return null;
    return data;
  } catch {
    return null;
  }
}

export function saveOrderDraft(
  marketCode: string,
  visitorId: string | null | undefined,
  draft: Omit<OrderDraftPayload, "v" | "savedAt">,
): void {
  if (typeof window === "undefined") return;
  try {
    const payload: OrderDraftPayload = {
      ...draft,
      v: ORDER_DRAFT_VERSION,
      savedAt: Date.now(),
    };
    localStorage.setItem(
      orderDraftStorageKey(marketCode, visitorId),
      JSON.stringify(payload),
    );
  } catch {
    /* quota / private mode — ignore */
  }
}

export function clearOrderDraft(marketCode: string, visitorId?: string | null): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(orderDraftStorageKey(marketCode, visitorId));
  } catch {
    /* ignore */
  }
}

/** Drop all Path A order drafts (e.g. fresh visitor session). */
export function clearAllOrderDrafts(): void {
  if (typeof window === "undefined") return;
  try {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(`${STORAGE_PREFIX}:`)) keys.push(k);
    }
    for (const k of keys) localStorage.removeItem(k);
  } catch {
    /* ignore */
  }
}

export function createDebouncedOrderDraftSaver(delayMs = 400): {
  schedule: (
    marketCode: string,
    visitorId: string | null | undefined,
    draft: Omit<OrderDraftPayload, "v" | "savedAt">,
  ) => void;
  flush: () => void;
  cancel: () => void;
} {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pending: {
    marketCode: string;
    visitorId: string | null | undefined;
    draft: Omit<OrderDraftPayload, "v" | "savedAt">;
  } | null = null;

  const flush = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (!pending) return;
    const { marketCode, visitorId, draft } = pending;
    pending = null;
    saveOrderDraft(marketCode, visitorId, draft);
  };

  return {
    schedule(marketCode, visitorId, draft) {
      pending = { marketCode, visitorId, draft };
      if (timer) clearTimeout(timer);
      timer = setTimeout(flush, delayMs);
    },
    flush,
    cancel() {
      if (timer) clearTimeout(timer);
      timer = null;
      pending = null;
    },
  };
}
