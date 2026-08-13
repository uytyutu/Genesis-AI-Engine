"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type ClientOrder = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  service_name?: string;
  status_label?: string;
  status?: string;
  product_kind?: string;
  product_id?: string | null;
  package_id?: string;
  superseded?: boolean;
  quality_state?: string;
};

export default function ClientWebsiteHubPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<ClientOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!getClientToken()) {
      router.replace("/client/login?next=/client/site");
      return;
    }
    try {
      const res = await fetch(`${API}/api/client/orders`, {
        headers: { ...clientAuthHeaders() },
        cache: "no-store",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body) || "load_failed");
      const list = (Array.isArray(body.orders) ? body.orders : []) as ClientOrder[];
      setOrders(
        list.filter((o) => {
          const kind = String(o.product_kind || "");
          if (kind === "shop" || o.package_id === "ecommerce_shop") return false;
          if (kind.startsWith("bot")) return false;
          if (String(o.status || "").toLowerCase() === "superseded") return false;
          if (o.superseded === true) return false;
          if (String(o.quality_state || "").toUpperCase() === "ARCHIVED") return false;
          return true;
        }),
      );
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "load_failed");
      setOrders([]);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <ClientWorkspaceShell
      title="Website"
      subtitle="Ihre Website verwalten: Kontakte, Design, Medien und Vorschau."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {orders === null ? (
        <p className="text-sm text-zinc-500">Laden…</p>
      ) : orders.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>Noch keine Website gekauft.</p>
          <Link
            href="/client/shop"
            className="mt-4 inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black"
          >
            Website ansehen
          </Link>
        </div>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2">
          {orders.map((o) => (
            <li
              key={o.order_id}
              className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-5"
            >
              <p className="text-[11px] font-medium uppercase tracking-wide text-zinc-500">
                Website
              </p>
              <p className="mt-1 text-lg font-semibold text-white">
                {o.business_name || o.service_name || o.package_name || "Website"}
              </p>
              <p className="mt-1 text-xs font-medium uppercase tracking-wide text-emerald-300">
                {o.status_label || o.status || "Active"}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href={`/client/websites/${o.order_id}/admin?section=website`}
                  className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                >
                  Einstellungen
                </Link>
                <Link
                  href={`/client/websites/${o.order_id}/admin?section=design`}
                  className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                >
                  Design / Logo
                </Link>
                {o.product_id ? (
                  <a
                    href={`${API}/api/factory/products/${o.product_id}/preview`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-xl border border-emerald-500/40 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-950/40"
                  >
                    Öffnen / Vorschau
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
