import { formatApiDetail } from "./formatApiError";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

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
      // Next rewrite returns 500 when backend is briefly down — retry.
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

export async function startOrderCheckout(orderId: string): Promise<string> {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  try {
    const { logCommerceEvent } = await import("./commerceFunnel");
    logCommerceEvent("checkout_start", null, "checkout", { order_id: orderId });
  } catch {
    /* optional */
  }
  const res = await fetch(`${API}/api/sales/orders/${orderId}/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      success_url: `${origin}/order/status/${orderId}?paid=1`,
      cancel_url: `${origin}/order/status/${orderId}`,
    }),
  });
  const body = await res.json();
  if (!res.ok) {
    throw new Error(formatApiDetail(body.detail) || "Не удалось начать оплату");
  }
  if (!body.checkout_url) {
    throw new Error("Нет ссылки на оплату");
  }
  return body.checkout_url as string;
}

export async function fetchPaymentReady(): Promise<boolean> {
  try {
    const res = await fetchJsonWithRetry("/api/sales/payment-status");
    const body = await res.json();
    return Boolean(body.configured);
  } catch {
    return false;
  }
}

export async function fetchPaymentInfo(): Promise<{ configured: boolean; sandbox: boolean }> {
  try {
    const res = await fetchJsonWithRetry("/api/sales/payment-status");
    const body = await res.json();
    return { configured: Boolean(body.configured), sandbox: Boolean(body.sandbox) };
  } catch {
    return { configured: false, sandbox: false };
  }
}
