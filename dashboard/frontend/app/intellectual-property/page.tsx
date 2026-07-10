import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Urheberrecht & Nutzungsrechte",
  "Übertragung und Nutzung von Projektergebnissen bei Virtus Core.",
  "/intellectual-property"
);

export default function IntellectualPropertyPage() {
  return (
    <LegalDocumentPage
      docId="intellectual-property"
      fallbackTitle="Urheberrecht & Nutzungsrechte"
      fallbackSubtitle="Was Sie nach Zahlung erhalten"
    />
  );
}
