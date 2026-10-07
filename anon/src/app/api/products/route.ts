import { json } from "@/lib/api";
import { PRODUCTS, formatMoney } from "@/lib/pricing";

export async function GET() {
  const items = Object.values(PRODUCTS)
    .filter((p) => p.sku !== "SEND_REVEAL" && p.pillar !== "pack")
    .map((p) => ({
      sku: p.sku,
      pillar: p.pillar,
      emoji: p.emoji,
      amountCents: p.amountCents,
      priceLabel: formatMoney(p.amountCents),
      nameKey: p.nameKey,
      descKey: p.descKey,
      impulse: p.impulse,
    }));
  return json({ products: items });
}
