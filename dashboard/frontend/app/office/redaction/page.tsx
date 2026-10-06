import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Schwärzung · Virtus Office · ${BRAND_NAME}`,
  "Personenbezogene Daten aus PDF entfernen — echte Redaction, nicht nur schwarze Flächen über Text.",
  "/office/redaction",
);

export default function OfficeRedactionPage() {
  return <OfficeServiceFlow kind="redaction" />;
}
