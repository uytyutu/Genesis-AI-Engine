import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Excel · Virtus Office · ${BRAND_NAME}`,
  "Tabelle oder Datendatei in bearbeitbares Excel überführen.",
  "/office/excel",
);

export default function OfficeExcelPage() {
  return <OfficeServiceFlow kind="excel" />;
}
