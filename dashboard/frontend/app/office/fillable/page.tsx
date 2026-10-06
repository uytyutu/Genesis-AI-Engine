import type { Metadata } from "next";
import { OfficeServiceFlow } from "../../components/office/OfficeServiceFlow";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Ausfüllbares PDF · Virtus Office · ${BRAND_NAME}`,
  "Gewöhnliches PDF → echtes AcroForm mit klickbaren Feldern.",
  "/office/fillable",
);

export default function OfficeFillablePage() {
  return <OfficeServiceFlow kind="fillable" />;
}
