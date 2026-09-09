import type { Metadata } from "next";
import { OfficeBewerbungPage } from "../../components/office/OfficeBewerbungPage";
import { BRAND_NAME } from "../../lib/publicBrand";
import { publicPageMetadata } from "../../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  `CV & Bewerbung · Virtus Office · ${BRAND_NAME}`,
  "Lebenslauf und Bewerbungsschreiben als vollständiges Paket für 24,90 €.",
  "/office/cv-bewerbung",
);

export default function OfficeCvBewerbungRoute() {
  return <OfficeBewerbungPage packageMode />;
}
