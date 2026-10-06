import type { Metadata } from "next";
import { OfficePdfProPage } from "../../components/office/OfficePdfProPage";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicPageMetadata } from "../../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  `PDF PRO · Virtus Office · ${BRAND_NAME}`,
  "PDF-Komplettpaket für Suche, Schwärzung, Formulare, Archiv und Qualitätsprüfung.",
  "/office/pdf-pro",
);

export default function OfficePdfProRoute() {
  return <OfficePdfProPage />;
}
