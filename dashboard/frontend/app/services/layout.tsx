import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Leistungen",
  "Leistungen von Virtus Core: fertige Business-Website bestellen und nächste Schritte für Ihr Unternehmen.",
  "/services"
);

export default function ServicesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
