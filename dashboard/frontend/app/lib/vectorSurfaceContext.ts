/**
 * Vector surface context — one assistant, many surfaces.
 */

export type VectorSurface =
  | "platform"
  | "website_admin"
  | "store_admin"
  | "customer"
  | "commerce_wizard";

export type VectorAction = {
  id: string;
  capability?: string;
  label: string;
  status: "live" | "coming" | string;
  kind:
    | "navigate_section"
    | "navigate_href"
    | "coming"
    | "set_learning"
    | "wizard_goto"
    | "noop"
    | string;
  section?: string;
  href?: string;
  coming?: string;
  value?: string;
  step_id?: string;
};

export type VectorDialogMessage = {
  role: "assistant" | "user" | string;
  text: string;
};

export type VectorDialogPayload = {
  ok: boolean;
  surface: VectorSurface | string;
  assistant: string;
  mode: string;
  dock?: "right" | "bottom" | string;
  learning_mode?: string | null;
  messages: VectorDialogMessage[];
  actions: VectorAction[];
  wizard?: {
    step_id: string;
    index: number;
    total: number;
    steps?: { id: string; done: boolean; coming?: string | null }[];
  } | null;
  setup?: {
    readiness_pct?: number;
    setup_pct?: number;
    product_count?: number;
  };
  business_setup?: BusinessSetupPayload | null;
  readiness_pct?: number;
  setup_pct?: number;
  honesty?: string;
  order_id?: string;
  error?: string;
};

export type VectorSetupStep = {
  id: string;
  label: string;
  done: boolean;
  actionable: boolean;
  weight: number;
  section: string;
  cta_label?: string;
  coming?: string;
  meta?: Record<string, unknown>;
};

export type VectorTip = {
  id: string;
  priority: number;
  message: string;
  section: string;
  cta_label?: string;
  coming?: string;
};

export type StoreSetupStatus = {
  ok: boolean;
  order_id: string;
  surface: VectorSurface | string;
  vector: {
    assistant: string;
    mode: string;
    greeting: string;
  };
  readiness_pct: number;
  setup_pct: number;
  product_count: number;
  customer_count: number;
  order_count: number;
  shop_pipeline?: string | null;
  steps: VectorSetupStep[];
  next_step: VectorSetupStep | null;
  tips: VectorTip[];
  commerce_ready: boolean;
  note?: string;
};

export type BusinessSetupItem = {
  id: string;
  label: string;
  done: boolean;
  weight: number;
  actionable?: boolean;
  coming?: string;
  action?: VectorAction;
  meta?: Record<string, unknown>;
};

export type LaunchChecklistItem = {
  id: string;
  label: string;
  done: boolean;
  why?: string;
  href?: string;
  upsell?: boolean;
};

export type BusinessSetupPayload = {
  ok: boolean;
  title: string;
  pct: number;
  bars?: { id: string; label: string; pct: number; done: boolean }[];
  items: BusinessSetupItem[];
  next: BusinessSetupItem | null;
  note?: string;
  launch?: {
    stage?: string;
    title?: string;
    items?: LaunchChecklistItem[];
    next?: LaunchChecklistItem | null;
    note?: string;
    standalone_soft?: boolean;
  };
};

export type VectorSurfaceContext = {
  surface: VectorSurface;
  role: "owner" | "staff" | "customer" | "visitor";
  orderId?: string;
  productKind?: "website" | "shop" | string;
  locale?: string;
  setup?: StoreSetupStatus | null;
};

export const VECTOR_LEARN_KEY = "virtus_vector_learn_v1";

export function loadVectorLearningMode(surface: string): "skip" | "show" | null {
  try {
    const raw = localStorage.getItem(`${VECTOR_LEARN_KEY}:${surface}`);
    if (raw === "skip" || raw === "show") return raw;
  } catch {
    /* ignore */
  }
  return null;
}

export function saveVectorLearningMode(
  surface: string,
  mode: "skip" | "show",
): void {
  try {
    localStorage.setItem(`${VECTOR_LEARN_KEY}:${surface}`, mode);
  } catch {
    /* ignore */
  }
}
