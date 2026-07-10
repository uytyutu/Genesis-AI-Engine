import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  "AGB",
  `Allgemeine Geschäftsbedingungen für Dienstleistungen von ${BRAND_NAME}.`,
  "/agb"
);

export default function AgbPage() {
  return (
    <LegalDocumentPage
      docId="agb"
      fallbackTitle="Allgemeine Geschäftsbedingungen (AGB)"
      fallbackSubtitle="Stand: Juli 2026"
    />
  );
}
