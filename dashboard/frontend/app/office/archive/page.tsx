import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Dokumenten-Archiv · Virtus Office · ${BRAND_NAME}`,
  "Mehrere Dokumente oder ZIP → Ordner, Umbenennung, ZIP + index.xlsx.",
  "/office/archive",
);

export default function OfficeArchivePage() {
  return <OfficeServiceFlow kind="archive" />;
}
