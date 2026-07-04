import { formatApiDetail } from "./formatApiError";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function startOrderCheckout(orderId: string): Promise<string> {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const res = await fetch(`${API}/api/sales/orders/${orderId}/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      success_url: `${origin}/order/status/${orderId}`,
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
    const res = await fetch(`${API}/api/sales/payment-status`);
    const body = await res.json();
    return Boolean(body.configured);
  } catch {
    return false;
  }
}

export async function fetchPaymentInfo(): Promise<{ configured: boolean; sandbox: boolean }> {
  try {
    const res = await fetch(`${API}/api/sales/payment-status`);
    const body = await res.json();
    return { configured: Boolean(body.configured), sandbox: Boolean(body.sandbox) };
  } catch {
    return { configured: false, sandbox: false };
  }
}
