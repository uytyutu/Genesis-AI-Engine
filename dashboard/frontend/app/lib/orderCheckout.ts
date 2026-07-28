import { formatApiDetail } from "./formatApiError";
import { publicApiBase } from "./publicApiBase";
import { SITE_URL } from "./siteConfig";

const API = publicApiBase();

const LEGACY_HOST_RE = /genesis-ai-engine\.vercel\.app/i;

function storefrontOrigin(): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    const origin = window.location.origin;
    if (!LEGACY_HOST_RE.test(origin)) return origin;
  }
  return SITE_URL.replace(/\/$/, "");
}

async function fetchJsonWithRetry(
  path: string,
  options?: { attempts?: number; delayMs?: number },
): Promise<Response> {
  const attempts = options?.attempts ?? 4;
  const delayMs = options?.delayMs ?? 400;
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(`${API}${path}`);
      if (res.status >= 500 && i < attempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
        continue;
      }
      return res;
    } catch (err) {
      lastErr = err;
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
        continue;
      }
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("fetch_failed");
}

export async function startOrderCheckout(
  orderId: string,
  options?: { successPath?: string; cancelPath?: string },
): Promise<string> {
  const origin = storefrontOrigin();
  try {
    const { logCommerceEvent } = await import("./commerceFunnel");
    // Path A back-compat + Order Experience A2.1
    logCommerceEvent("checkout_start", null, "checkout", { order_id: orderId });
    logCommerceEvent("stripe_redirect_started", null, "checkout", { order_id: orderId });
  } catch {
    /* optional */
  }
  const successPath =
    options?.successPath || `/order/status/${orderId}?paid=1`;
  const cancelPath =
    options?.cancelPath || `/order/status/${orderId}?canceled=1`;
  const res = await fetch(`${API}/api/sales/orders/${orderId}/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      success_url: `${origin}${successPath.startsWith("/") ? successPath : `/${successPath}`}`,
      cancel_url: `${origin}${cancelPath.startsWith("/") ? cancelPath : `/${cancelPath}`}`,
    }),
  });
  const body = await res.json();
  if (!res.ok) {
    throw new Error(
      formatApiDetail(body.detail) || "Zahlung konnte nicht gestartet werden",
    );
  }
  const url = String(body.checkout_url || "");
  if (!url) {
    throw new Error("Keine Zahlungslink erhalten");
  }
  if (LEGACY_HOST_RE.test(url) || /\.vercel\.app/i.test(url)) {
    throw new Error(
      "Zahlung lieferte eine veraltete Adresse. GENESIS_PUBLIC_URL muss auf die Live-Domain zeigen.",
    );
  }
  const sandbox = Boolean(body.sandbox);
  const isStripe = /^https:\/\/checkout\.stripe\.com\//i.test(url);
  if (!sandbox && !isStripe) {
    throw new Error("Zahlung falsch konfiguriert: Stripe Checkout erwartet");
  }
  return url;
}

export async function fetchPaymentReady(): Promise<boolean> {
  try {
    const res = await fetchJsonWithRetry("/api/sales/payment-status");
    const body = await res.json();
    if (body.stripe_ready) return true;
    if (body.sandbox && body.configured) return true;
    return Boolean(body.configured && body.provider === "stripe");
  } catch {
    return false;
  }
}

export async function fetchPaymentInfo(): Promise<{
  configured: boolean;
  sandbox: boolean;
  stripe_ready: boolean;
}> {
  try {
    const res = await fetchJsonWithRetry("/api/sales/payment-status");
    const body = await res.json();
    return {
      configured: Boolean(body.configured),
      sandbox: Boolean(body.sandbox),
      stripe_ready: Boolean(body.stripe_ready),
    };
  } catch {
    return { configured: false, sandbox: false, stripe_ready: false };
  }
}
