import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Landing bestellen",
  "Landing Page · digitaler Neustart: Preise auf /order, Bestellstatus, Online-Zahlung wenn verbunden.",
  "/order"
);

export default function OrderLayout({ children }: { children: React.ReactNode }) {
  return children;
}
