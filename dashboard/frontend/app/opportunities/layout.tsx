import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Возможности — Virtus Core",
  description: "Opportunity Engine: журнал возможностей и источников дохода.",
};

export default function OpportunitiesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
