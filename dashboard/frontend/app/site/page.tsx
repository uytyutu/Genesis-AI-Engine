import type { Metadata } from "next";
import { SitePage } from "./SitePage";

export const metadata: Metadata = {
  title: "Сайт для вашего бизнеса — Genesis",
  description:
    "Современный лендинг под ключ: цена сразу, оплата онлайн, статус заказа, срок от 48 часов.",
};

export default function Page() {
  return <SitePage />;
}
