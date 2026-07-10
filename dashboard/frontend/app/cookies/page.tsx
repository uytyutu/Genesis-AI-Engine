import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Cookie-Richtlinie",
  "Cookie-Richtlinie für Virtus Core.",
  "/cookies"
);

export default function CookiesPage() {
  return (
    <LegalDocumentPage
      docId="cookies"
      fallbackTitle="Cookie-Richtlinie"
      fallbackSubtitle="Welche Cookies wir verwenden"
    />
  );
}
