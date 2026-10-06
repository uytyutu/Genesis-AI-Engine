import type { Metadata } from "next";
import { OfficeLebenslaufLanding } from "../../components/office/OfficeLebenslaufLanding";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Lebenslauf · Virtus Office · ${BRAND_NAME}`,
  "Professionellen Lebenslauf erstellen oder verbessern — PDF + DOCX.",
  "/office/lebenslauf",
);

export default function OfficeLebenslaufPage() {
  return <OfficeLebenslaufLanding />;
}
