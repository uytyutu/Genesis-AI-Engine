import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Produkte & Leistungen",
  "Virtus Core Mission 1: digitale Firma mit Vector und Website-Bestellung 299 / 599 / 999 €. Virtus Studio — in Entwicklung.",
  "/products"
);

export default function ProductsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
