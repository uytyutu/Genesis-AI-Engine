import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Website bestellen · Virtus Core",
  "Professionelle Website, Online-Shop oder AI Assistant bestellen — Preise, Bestellstatus und Zahlung.",
  "/order"
);

export default function OrderLayout({ children }: { children: React.ReactNode }) {
  return children;
}
