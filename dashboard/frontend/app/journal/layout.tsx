import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Журнал — Virtus Core",
  description: "Доход и задачи цифровой фермы в реальном времени.",
};

export default function JournalLayout({ children }: { children: React.ReactNode }) {
  return children;
}
