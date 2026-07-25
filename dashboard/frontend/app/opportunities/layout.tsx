import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Возможности — Virtus Core",
  description:
    "Marketplace возможностей: Affiliate · Report · Content · API · Work — не ферма разметки.",
};

export default function OpportunitiesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
