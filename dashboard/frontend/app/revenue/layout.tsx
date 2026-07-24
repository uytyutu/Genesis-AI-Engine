import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Доход — Virtus Core",
  description: "Revenue Lab: источники, возможности, ключи CEO и пакеты Commercial API.",
};

export default function RevenueLayout({ children }: { children: React.ReactNode }) {
  return children;
}
