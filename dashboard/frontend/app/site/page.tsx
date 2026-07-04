import type { Metadata } from "next";
import { SitePage } from "./SitePage";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Сайт для вашего бизнеса",
  "Современный лендинг под ключ: цена сразу, оплата онлайн, статус заказа, срок от 48 часов.",
  "/site"
);

export default function Page() {
  return <SitePage />;
}
