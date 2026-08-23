"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { clientAuthHeaders, getClientToken } from "../../lib/clientAuth";
import { listStoredOrders } from "../../lib/orderHistory";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type OrderStatus = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  service_name?: string;
  package_id?: string | null;
  product_kind?: string;
  status?: string;
  status_label?: string;
  price_label?: string;
  paid?: boolean;
  eta_label?: string | null;
  download_ready?: boolean;
  download_url?: string | null;
  download_bytes?: number | null;
  generated_at?: string | null;
  download_label?: string | null;
  client_message?: string | null;
};

function formatBytes(n: number | null | undefined): string {
  if (n == null || n <= 0) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ClientDownloadsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<OrderStatus[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [source, setSource] = useState<"account" | "local">("account");

  const refresh = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      if (getClientToken()) {
        const res = await fetch(`${API}/api/client/orders`, {
          headers: { ...clientAuthHeaders() },
          cache: "no-store",
        });
        const body = await res.json().catch(() => ({}));
        if (res.status === 401) {
          router.replace("/client/login");
          return;
        }
        if (res.ok && Array.isArray(body.orders)) {
          setRows(body.orders as OrderStatus[]);
          setSource("account");
          return;
        }
      }
      // Fallback: localStorage history if not logged in / empty account
      const stored = listStoredOrders();
      setSource("local");
      if (stored.length === 0) {
        setRows([]);
        return;
      }
      const settled = await Promise.all(
        stored.map(async (o) => {
          try {
            const res = await fetch(`${API}/api/sales/orders/${o.order_id}/status`);
            if (!res.ok) {
              return {
                order_id: o.order_id,
                business_name: o.business_name,
                package_name: o.package_name,
                status: o.status || "unknown",
                status_label: "Status unavailable",
                download_ready: false,
              } as OrderStatus;
            }
            return (await res.json()) as OrderStatus;
          } catch {
            return {
              order_id: o.order_id,
              package_name: o.package_name,
              status: "offline",
              download_ready: false,
            } as OrderStatus;
          }
        }),
      );
      setRows(settled);
    } catch {
      setError("Could not load downloads. Start Virtus Core and try again.");
    } finally {
      setBusy(false);
    }
  }, [router]);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 8000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <ClientWorkspaceShell
      title="Downloads"
      subtitle={
        source === "account"
          ? "Файлы с вашего аккаунта — скачать, когда результат готов."
          : "Локальная история браузера (войдите, чтобы видеть заказы аккаунта)."
      }
    >
      <div className="mb-4 flex flex-wrap items-center gap-3 text-sm">
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded-xl border border-white/15 px-3 py-1.5 text-white hover:bg-white/5"
        >
          Refresh
        </button>
        <Link href="/client/products" className="text-emerald-300 hover:underline">
          My Products
        </Link>
        <Link href="/site" className="text-zinc-400 hover:underline">
          Storefront
        </Link>
      </div>
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {busy && rows.length === 0 ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>Пока нет загрузок.</p>
          <Link href="/client/shop" className="mt-3 inline-block text-emerald-300 hover:underline">
            Магазин услуг →
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {rows.map((o) => (
            <li
              key={o.order_id}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-base font-semibold text-white">
                    {o.service_name || o.package_name || o.business_name || o.order_id}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {o.status_label || o.status}
                    {o.eta_label ? ` · ETA ${o.eta_label}` : ""}
                    {o.download_bytes ? ` · ${formatBytes(o.download_bytes)}` : ""}
                  </p>
                  {o.client_message ? (
                    <p className="mt-2 text-sm text-zinc-400">{o.client_message}</p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link
                    href={`/order/status/${o.order_id}`}
                    className="rounded-xl border border-white/15 px-3 py-2 text-sm text-white hover:bg-white/5"
                  >
                    Status
                  </Link>
                  {o.download_ready && o.download_url ? (
                    <a
                      href={`${API}${o.download_url}`}
                      className="rounded-xl bg-emerald-500 px-3 py-2 text-sm font-semibold text-black"
                    >
                      Download
                    </a>
                  ) : (
                    <span className="rounded-xl border border-white/10 px-3 py-2 text-sm text-zinc-500">
                      {o.download_label || "In progress"}
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
