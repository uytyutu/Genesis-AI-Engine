import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "KI-Hinweis",
  "Hinweise zur Nutzung von KI bei Virtus Core und Vector.",
  "/ai-disclaimer"
);

export default function AiDisclaimerPage() {
  return (
    <LegalDocumentPage
      docId="ai-disclaimer"
      fallbackTitle="KI-Hinweis"
      fallbackSubtitle="Transparenz bei KI-gestützten Dienstleistungen"
    />
  );
}
