import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Заказать сайт",
  "Закажите лендинг для бизнеса: цена сразу на /order, статус заказа. Онлайн-оплата — когда подключена.",
  "/order"
);

export default function OrderLayout({ children }: { children: React.ReactNode }) {
  return children;
}
