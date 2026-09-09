import type { Metadata } from "next";
import { OfficeSalesKitPage } from "../../components/office/OfficeSalesKitPage";
import { publicPageMetadata } from "../../lib/publicMetadata";
import { BRAND_NAME } from "../../lib/publicBrand";

export const metadata: Metadata = publicPageMetadata(
  `Sales Kit · Virtus Office · ${BRAND_NAME}`,
  "Professionelle Vertriebsunterlagen aus Ihren Unternehmensdaten — Basic, Business, Professional.",
  "/office/sales-kit",
);

export default function OfficeSalesKitRoute() {
  return <OfficeSalesKitPage />;
}
