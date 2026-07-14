import { Suspense } from "react";
import OwnerGateClient from "./OwnerGateClient";

export default function OwnerGatePage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-genesis-bg" />}>
      <OwnerGateClient />
    </Suspense>
  );
}
