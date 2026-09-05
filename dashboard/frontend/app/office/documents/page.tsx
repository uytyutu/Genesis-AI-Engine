import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Dokumente · Virtus Office · ${BRAND_NAME}`,
  "Scan oder Text in ein klares Word-Dokument umwandeln.",
  "/office/documents",
);

export default function OfficeDocumentsPage() {
  return <OfficeServiceFlow kind="documents" />;
}
