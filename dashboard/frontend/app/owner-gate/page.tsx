import type { Metadata } from "next";
import { Suspense } from "react";
import OwnerGateClient from "./OwnerGateClient";

export const metadata: Metadata = {
  title: "Owner gate",
  robots: { index: false, follow: false, nocache: true },
};

export default function OwnerGatePage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-genesis-bg" />}>
      <OwnerGateClient />
    </Suspense>
  );
}
