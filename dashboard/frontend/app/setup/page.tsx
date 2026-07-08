"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GenesisSetupWizard } from "../components/GenesisSetupWizard";

/** Owner-only: workforce hiring — never linked from public /site, not indexed */
export default function OwnerSetupPage() {
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    const host = window.location.hostname;
    setAllowed(host === "localhost" || host === "127.0.0.1");
  }, []);

  if (allowed === null) {
    return null;
  }

  if (!allowed) {
    return (
      <main className="mx-auto max-w-lg px-4 py-16 text-center">
        <h1 className="text-xl font-semibold text-white">Owner only</h1>
        <p className="mt-3 text-sm text-genesis-muted">
          Эта страница доступна только владельцу. Посетители общаются с Genesis на сайте — без
          настроек и API.
        </p>
        <Link href="/site" className="mt-6 inline-block text-genesis-accent hover:underline">
          На сайт
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6">
      <p className="mb-4 text-center text-xs uppercase tracking-widest text-genesis-muted">
        Owner Mode — скрыто от посетителей
      </p>
      <GenesisSetupWizard />
    </main>
  );
}
