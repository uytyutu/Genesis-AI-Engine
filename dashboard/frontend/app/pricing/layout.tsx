import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${BRAND_NAME} Platform`,
  `${BRAND_NAME} Platform — подписки и возможности. Сравнение тарифов и ранний доступ.`,
  "/products"
);

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
