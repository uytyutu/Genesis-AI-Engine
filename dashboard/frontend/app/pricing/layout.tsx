import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `${BRAND_NAME} Platform`,
  `${BRAND_NAME} Platform — разговор с Vector и заказ лендинга. Virtus Studio в разработке.`,
  "/pricing"
);

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
