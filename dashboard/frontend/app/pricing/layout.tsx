import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Genesis Platform",
  "Genesis Platform — подписки и возможности. Сравнение тарифов и ранний доступ.",
  "/products"
);

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
