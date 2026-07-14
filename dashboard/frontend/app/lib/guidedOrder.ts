import { formatApiDetail } from "./formatApiError";
import { buildGuidedSalesBrief } from "./guidedJourney";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export type GuidedPackage = {
  id: string;
  name: string;
  price_eur: number;
  price_label?: string;
  currency?: string;
};

export async function fetchGuidedBasicPackage(): Promise<GuidedPackage | null> {
  try {
    const res = await fetch(`${API}/api/sales/packages`);
    const body = await res.json();
    const basic = (body.packages as GuidedPackage[] | undefined)?.find((p) => p.id === "basic");
    return basic ?? null;
  } catch {
    return null;
  }
}

export async function createGuidedSiteOrder(params: {
  businessName: string;
  email: string;
  visitorId: string;
  goalLabel: string;
  logoChoice: "yes" | "no" | "auto";
  productId: string;
  description: string;
  city?: string;
  phone?: string;
  extraWishes?: string;
}): Promise<{ orderId: string; priceEur: number; packageName: string; priceLabel?: string }> {
  const res = await fetch(`${API}/api/sales/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      business_name: params.businessName.trim(),
      description: params.description.trim(),
      email: params.email.trim(),
      city: params.city?.trim() || undefined,
      phone: params.phone?.trim() || undefined,
      extra_wishes: params.extraWishes?.trim() || undefined,
      package_id: "basic",
      visitor_id: params.visitorId,
      needs_logo: params.logoChoice === "no",
      needs_domain: false,
      product_id: params.productId,
    }),
  });
  const body = await res.json();
  if (!res.ok) {
    throw new Error(formatApiDetail(body.detail) || "Не удалось оформить заказ");
  }
  return {
    orderId: body.order_id as string,
    priceEur: Number(body.price_eur),
    packageName: body.package_name as string,
    priceLabel: body.price_label as string | undefined,
  };
}
