import type { Metadata } from "next";
import { OpenExperience } from "@/components/OpenExperience";

export const metadata: Metadata = {
  title: "💌 Someone sent you something",
  description: "Open your gift from ANON.",
  robots: { index: false, follow: false },
  openGraph: {
    title: "💌 Someone sent you something",
    description: "Open your gift from ANON.",
  },
};

export default async function OpenPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <OpenExperience token={token} />;
}
