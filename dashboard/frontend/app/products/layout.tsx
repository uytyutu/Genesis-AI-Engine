import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Virtus Core — подписка",
  "Что умеет Virtus Core, сравнение тарифов Free / Basic / Pro / Business / Enterprise. Услуга или подписка — что выгоднее.",
  "/products"
);

export default function ProductsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
