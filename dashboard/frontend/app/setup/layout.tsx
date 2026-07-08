import type { Metadata } from "next";
import { BRAND_NAME } from "../lib/publicBrand";

export const metadata: Metadata = {
  title: `${BRAND_NAME} Owner Setup`,
  robots: { index: false, follow: false },
};

export default function OwnerSetupLayout({ children }: { children: React.ReactNode }) {
  return children;
}
