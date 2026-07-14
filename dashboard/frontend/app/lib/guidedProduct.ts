import { formatApiDetail } from "./formatApiError";
import { type GuidedCommerceState } from "./guidedCommerce";
import { buildGuidedSalesBrief } from "./guidedJourney";
import { publicApiBase } from "./publicApiBase";

const API = publicApiBase();

export function buildGuidedFactoryBrief(state: GuidedCommerceState): string {
  return buildGuidedSalesBrief(state);
}

/** Create draft Factory Product — same object shown in preview and sold at checkout. */
export async function ensureGuidedDraftProduct(
  state: GuidedCommerceState,
): Promise<string> {
  if (state.productId) return state.productId;
  const name = state.companyName.trim();
  if (!name || !state.goalId) {
    throw new Error("Сначала ответьте на вопросы о бизнесе и видении");
  }
  const res = await fetch(`${API}/api/factory/intent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_type: "landing-page",
      description: buildGuidedFactoryBrief(state),
    }),
  });
  const body = await res.json();
  if (!res.ok) {
    throw new Error(formatApiDetail(body.detail) || "Не удалось собрать черновик сайта");
  }
  const productId = body.product_id as string | undefined;
  if (!productId) {
    throw new Error("Не удалось получить черновик");
  }
  return productId;
}

export function guidedProductPreviewUrl(productId: string): string {
  return `${API}/api/factory/products/${encodeURIComponent(productId)}/preview`;
}
