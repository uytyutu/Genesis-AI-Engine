import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();
const ACCOUNT_KEY = "viewora_account_id";

export function getAccountId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCOUNT_KEY);
}

export function setAccountId(id: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCOUNT_KEY, id);
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = body?.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : detail?.message || detail?.code || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body as T;
}

export type VieworaCatalog = {
  ok: boolean;
  name: string;
  tagline: string;
  positioning: string;
  plans: Array<{
    id: string;
    name: string;
    monthly_eur: number;
    credits: number;
    creations?: number | null;
    highlight?: string;
    popular?: boolean;
    features: string[];
  }>;
  credit_packs: Array<{ id: string; eur: number; credits: number }>;
  creation_types: Array<{ id: string; label: string; emoji: string; credits: number }>;
  modes: Array<{ id: string; label: string; blurb: string }>;
  visual_dna: Record<string, string[]>;
  product_ad_styles: string[];
  reality: {
    package_generation: boolean;
    storyboard_preview: boolean;
    mp4_render: boolean;
    note: string;
  };
};

export async function fetchCatalog() {
  return jsonFetch<VieworaCatalog>("/api/viewora/catalog");
}

export async function fetchAccount(accountId?: string | null) {
  const body = await jsonFetch<{
    ok: boolean;
    account: {
      id: string;
      plan_id: string;
      credits: number;
      free_creations_left: number;
      email?: string;
    };
    plan: { id: string; name: string; monthly_eur: number };
    payment: {
      stripe_ready: boolean;
      demo_payment_available: boolean;
      payment_mode_default: string;
    };
  }>("/api/viewora/account", {
    method: "POST",
    body: JSON.stringify({ account_id: accountId || getAccountId() }),
  });
  if (body.account?.id) setAccountId(body.account.id);
  return body;
}

export async function createStudio(payload: {
  brief: string;
  creation_type?: string;
  mode?: string | null;
  visual_dna?: Record<string, string> | null;
  product_style?: string | null;
  action?: string;
}) {
  const body = await jsonFetch<{
    ok: boolean;
    account: {
      id: string;
      plan_id: string;
      credits: number;
      free_creations_left: number;
    };
    job_id: string;
    action: string;
    result: Record<string, unknown>;
  }>("/api/viewora/create", {
    method: "POST",
    body: JSON.stringify({
      account_id: getAccountId(),
      ...payload,
    }),
  });
  if (body.account?.id) setAccountId(body.account.id);
  return body;
}

export async function startCheckout(payload: {
  kind: "plan" | "credits";
  sku: string;
  email?: string;
  prefer_demo?: boolean;
}) {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return jsonFetch<{
    ok: boolean;
    order_id: string;
    checkout_url: string;
    amount_eur: number;
    label: string;
    provider: string;
    payment_mode: string;
    demo_payment_available?: boolean;
    account_id: string;
  }>("/api/viewora/checkout", {
    method: "POST",
    body: JSON.stringify({
      account_id: getAccountId(),
      email: payload.email || "",
      kind: payload.kind,
      sku: payload.sku,
      prefer_demo: payload.prefer_demo || false,
      success_url: `${origin}/viewora/success?paid=1&order_id={ORDER}`,
      cancel_url: `${origin}/viewora/pricing?canceled=1`,
    }),
  }).then((out) => {
    if (out.account_id) setAccountId(out.account_id);
    const url = (out.checkout_url || "").replace("{ORDER}", out.order_id);
    return { ...out, checkout_url: url };
  });
}

export async function fetchOrder(orderId: string) {
  return jsonFetch<{ ok: boolean; order: Record<string, unknown> }>(
    `/api/viewora/orders/${orderId}`
  );
}

export async function payDemo(orderId: string) {
  return jsonFetch<{
    ok: boolean;
    payment_mode: string;
    account: { id: string; plan_id: string; credits: number };
    note?: string;
  }>(`/api/viewora/orders/${orderId}/pay-demo`, { method: "POST" });
}

export async function paySandbox(orderId: string) {
  return jsonFetch<{
    ok: boolean;
    payment_mode: string;
    account: { id: string; plan_id: string; credits: number };
  }>(`/api/viewora/orders/${orderId}/pay-sandbox`, { method: "POST" });
}
