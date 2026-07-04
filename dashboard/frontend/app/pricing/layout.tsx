import type { Metadata } from "next";
import { publicPageMetadata } from "../lib/publicMetadata";

export const metadata: Metadata = publicPageMetadata(
  "Platform",
  "Genesis Platform — ранний доступ. Подписки откроются после публичного запуска.",
  "/pricing"
);

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
