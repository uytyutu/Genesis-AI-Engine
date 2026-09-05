import type { Metadata } from "next";
import { OfficeBewerbungPage } from "../../components/office/OfficeBewerbungPage";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Bewerbung Office · Virtus Office · ${BRAND_NAME}`,
  "Lebenslauf erstellen oder verbessern, Bewerbungsschreiben und Bewerbung-Paket — nur aus Ihren Angaben.",
  "/office/bewerbung",
);

export default function VirtusBewerbungRoute() {
  return <OfficeBewerbungPage />;
}
