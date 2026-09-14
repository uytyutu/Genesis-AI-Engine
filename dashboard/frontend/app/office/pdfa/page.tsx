import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `PDF/A-2b · Virtus Office · ${BRAND_NAME}`,
  "Dokument → PDF/A-2b Archiv (strukturell geprüft). Kein veraPDF-Zertifikat.",
  "/office/pdfa",
);

export default function OfficePdfAPage() {
  return <OfficeServiceFlow kind="pdfa" />;
}
