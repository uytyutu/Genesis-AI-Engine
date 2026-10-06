import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Durchsuchbares PDF · Virtus Office · ${BRAND_NAME}`,
  "Scan oder Bild-PDF → durchsuchbares PDF mit Textschicht (Ctrl+F).",
  "/office/searchable",
);

export default function OfficeSearchablePage() {
  return <OfficeServiceFlow kind="searchable" />;
}
