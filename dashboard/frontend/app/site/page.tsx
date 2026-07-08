import type { Metadata } from "next";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Genesis — расскажите, что хотите создать",
  "ИИ-проводник Genesis: объяснит продукт, подберёт решение, покажет цену. Сайты для бизнеса — от 48 часов.",
  "/site"
);

export default function Page() {
  return <SitePage />;
}
