import type { Metadata } from "next";
import { OfficeHome } from "../components/office/OfficeHome";
import { publicPageMetadata } from "../lib/publicMetadata";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Virtus Office · ${BRAND_NAME}`,
  "Ihr digitaler Büroservice — Übersetzung, Lebenslauf, Bewerbung, Dokumente, Excel.",
  "/office",
);

export default function VirtusOfficePage() {
  return <OfficeHome />;
}
