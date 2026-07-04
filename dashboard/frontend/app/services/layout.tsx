import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Услуги",
  "Услуги Genesis: заказ сайта под ключ и направления развития компании.",
  "/services"
);

export default function ServicesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
