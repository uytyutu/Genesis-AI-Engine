import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Что доступно сейчас",
  "Virtus Core Mission 1: цифровая компания с Vector и заказ лендинга 350 / 650 / 1200 €. Virtus Studio — в разработке.",
  "/products"
);

export default function ProductsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
