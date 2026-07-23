"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { ASSISTANT_NAME } from "../../lib/publicBrand";

type MyProduct = {
  product_id: string;
  product_type: string;
  display_name: string;
  status: string;
  source: string;
};

function openHref(p: MyProduct) {
  if (p.product_type === "chatbot" || p.product_id === "prod_chatbot") {
    return "/projects/chatbot";
  }
  if (p.product_type === "website" || p.product_id === "prod_website") {
    return "/client/orders";
  }
  return "/client";
}

export default function ClientProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState<MyProduct[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setProducts(await portalFetch<MyProduct[]>("/portal/my-products"));
    } catch (err) {
      if (err instanceof PortalApiError && err.status === 401) {
        router.replace("/client/login");
        return;
      }
      if (err instanceof PortalApiError) setError(err.detail);
      else if (err instanceof Error) setError(err.message);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ClientWorkspaceShell
      title="My Products"
      subtitle="Cards for everything you own in Virtus Core."
    >
      {error ? (
        <p className="mb-4 text-sm text-rose-200">{error}</p>
      ) : null}
      {products === null ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : products.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>You have no products yet.</p>
          <p className="mt-2">
            After your first purchase or activation, product cards appear here.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/order"
              className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
            >
              Order Landing
            </Link>
            <Link
              href="/projects/chatbot/setup"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
            >
              Activate {ASSISTANT_NAME}
            </Link>
          </div>
        </div>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {products.map((p) => (
            <li
              key={p.product_id}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-lg font-semibold text-white">{p.display_name}</p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-emerald-300">
                Active
              </p>
              <p className="mt-2 flex-1 text-sm text-zinc-500">
                via {p.source}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={openHref(p)}
                  className="rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-semibold text-black hover:brightness-110"
                >
                  Open
                </Link>
                <Link
                  href={
                    p.product_type === "chatbot"
                      ? "/projects/chatbot/setup"
                      : "/client/orders"
                  }
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-sm text-zinc-200 hover:bg-white/5"
                >
                  Manage
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
