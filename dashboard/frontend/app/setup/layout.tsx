import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Genesis Owner Setup",
  robots: { index: false, follow: false },
};

export default function OwnerSetupLayout({ children }: { children: React.ReactNode }) {
  return children;
}
