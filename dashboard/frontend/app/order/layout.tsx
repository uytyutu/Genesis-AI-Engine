import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Заказать сайт",
  "Закажите лендинг для бизнеса: цена сразу, оплата онлайн, статус заказа.",
  "/order"
);

export default function OrderLayout({ children }: { children: React.ReactNode }) {
  return children;
}
