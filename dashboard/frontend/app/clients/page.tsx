"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function ClientsToUsers() {
  const router = useRouter();
  const sp = useSearchParams();
  const id = (sp.get("id") || "").trim();
  const q = (sp.get("q") || "").trim();

  useEffect(() => {
    const params = new URLSearchParams();
    if (id) params.set("id", id);
    if (q) params.set("q", q);
    const qs = params.toString();
    // Primitive deps only — depending on `sp` object retriggers forever.
    router.replace(qs ? `/users?${qs}` : "/users");
  }, [router, id, q]);

  return <main className="p-8 text-sm text-zinc-400">Переход к Owner Users…</main>;
}

/** Legacy /clients → /users (MC 2.0 Owner Users desk). */
export default function ClientsRedirectPage() {
  return (
    <Suspense fallback={<main className="p-8 text-sm text-zinc-400">…</main>}>
      <ClientsToUsers />
    </Suspense>
  );
}
