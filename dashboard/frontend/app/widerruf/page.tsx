import type { Metadata } from "next";
import { LegalDocumentPage } from "../components/LegalDocumentPage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Widerrufsbelehrung",
  "Widerrufsrecht für Verbraucher bei Virtus Core.",
  "/widerruf"
);

export default function WiderrufPage() {
  return (
    <LegalDocumentPage
      docId="widerruf"
      fallbackTitle="Widerrufsbelehrung"
      fallbackSubtitle="Informationen zum Widerrufsrecht"
    />
  );
}
