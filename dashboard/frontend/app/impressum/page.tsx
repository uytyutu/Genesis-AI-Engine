import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Impressum",
  "Impressum und Anbieterkennzeichnung gemäß § 5 DDG.",
  "/impressum"
);

export default function ImpressumPage() {
  return (
    <LegalDocumentPage
      docId="impressum"
      fallbackTitle="Impressum"
      fallbackSubtitle="Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz)"
    />
  );
}
