import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Услуги",
  "Услуги Virtus Core: заказ сайта под ключ и направления развития компании.",
  "/services"
);

export default function ServicesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
