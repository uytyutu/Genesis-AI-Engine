import type { Metadata } from "next";
import { Suspense } from "react";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `App Store für Unternehmen · ${BRAND_NAME}`,
  `Module verbinden — Websites, AI-Chatbots, Automatisierung. Vector kostenlos testen. Website ab 499 € · AI Store ab 799 €. KI-gestützte Lieferung mit Änderungswünschen nach dem Kauf.`,
  "/site"
);

export default function Page() {
  return (
    <Suspense fallback={null}>
      <SitePage />
    </Suspense>
  );
}
