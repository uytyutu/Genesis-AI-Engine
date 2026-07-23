"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { listStoredOrders, type StoredOrderRef } from "../../lib/orderHistory";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type OrderStatus = {
  order_id: string;
  business_name?: string;
  package_name?: string;
  package_id?: string | null;
  product_kind?: string;
  status?: string;
  status_label?: string;
  price_label?: string;
  paid?: boolean;
  paid_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
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

function formatWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function ClientDownloadsPage() {
  const [refs, setRefs] = useState<StoredOrderRef[]>([]);
  const [rows, setRows] = useState<OrderStatus[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const stored = listStoredOrders();
    setRefs(stored);
    if (stored.length === 0) {
      setRows([]);
      setBusy(false);
      return;
    }
    setBusy(true);
    setError("");
    try {
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
                price_label: o.price_label,
                download_ready: false,
              } as OrderStatus;
            }
            return (await res.json()) as OrderStatus;
          } catch {
            return {
              order_id: o.order_id,
              business_name: o.business_name,
              package_name: o.package_name,
              status: "offline",
              status_label: "API offline",
              download_ready: false,
            } as OrderStatus;
          }
        })
      );
      setRows(settled);
    } catch {
      setError("Could not load downloads. Start Virtus Core and try again.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const t = window.setInterval(() => void refresh(), 8000);
    return () => window.clearInterval(t);
  }, [refresh]);

  return (
    <ClientWorkspaceShell
      title="Downloads"
      subtitle="Your paid website ZIPs and repair order status — ready when generation finishes."
    >
      <div className="mb-4 flex flex-wrap items-center gap-3 text-sm">
        <button
          type="button"
          onClick={() => void refresh()}
          className="rounded-xl border border-white/15 px-3 py-1.5 text-white hover:bg-white/5"
        >
          Refresh
        </button>
        <Link href="/order/history" className="text-emerald-300 hover:underline">
          Order history →
        </Link>
        <Link href="/order" className="text-zinc-400 hover:underline">
          New order
        </Link>
      </div>

      {error ? <p className="mb-3 text-sm text-rose-300">{error}</p> : null}
      {busy && rows.length === 0 ? (
        <p className="text-sm text-zinc-400">Loading downloads…</p>
      ) : null}

      {!busy && refs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>No orders in this browser yet.</p>
          <p className="mt-2">
            After you pay for a website, open the order status page once — then the ZIP
            appears here with Download.
          </p>
          <Link
            href="/order"
            className="mt-4 inline-flex rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
          >
            Order a website →
          </Link>
        </div>
      ) : null}

      <ul className="space-y-4">
        {rows.map((row) => {
          const isRepair = row.product_kind === "repair" || String(row.package_id || "").startsWith("repair_");
          const generating =
            !row.download_ready &&
            !isRepair &&
            row.paid &&
            ["paid", "in_production", "generating"].includes(String(row.status || ""));
          const readyLabel =
            row.download_label ||
            (row.download_ready ? "Ready for download" : generating ? "generating..." : null);
          return (
            <li
              key={row.order_id}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 sm:p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-mono text-xs text-zinc-500">№ {row.order_id}</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {row.business_name || "Order"}
                  </p>
                  <p className="mt-1 text-sm text-zinc-400">
                    {row.package_name || row.package_id || "—"}
                    {row.price_label ? ` · ${row.price_label}` : ""}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p className="font-medium text-emerald-200">
                    {row.status_label || row.status || "—"}
                  </p>
                  {readyLabel ? (
                    <p
                      className={
                        row.download_ready
                          ? "mt-1 text-xs font-semibold text-emerald-300"
                          : "mt-1 text-xs font-semibold text-amber-200"
                      }
                    >
                      {readyLabel}
                    </p>
                  ) : null}
                </div>
              </div>

              <dl className="mt-4 grid gap-2 text-xs text-zinc-400 sm:grid-cols-3">
                <div>
                  <dt className="uppercase tracking-wide text-zinc-600">Generated</dt>
                  <dd className="mt-0.5 text-zinc-200">
                    {formatWhen(row.generated_at || row.updated_at || row.paid_at || row.created_at)}
                  </dd>
                </div>
                <div>
                  <dt className="uppercase tracking-wide text-zinc-600">Archive size</dt>
                  <dd className="mt-0.5 text-zinc-200">
                    {isRepair ? "n/a (operator repair)" : formatBytes(row.download_bytes)}
                  </dd>
                </div>
                <div>
                  <dt className="uppercase tracking-wide text-zinc-600">Paid</dt>
                  <dd className="mt-0.5 text-zinc-200">{formatWhen(row.paid_at)}</dd>
                </div>
              </dl>

              {row.client_message ? (
                <p className="mt-3 text-sm text-zinc-400">{row.client_message}</p>
              ) : null}

              <div className="mt-4 flex flex-wrap gap-2">
                {isRepair ? (
                  <Link
                    href={`/order/status/${row.order_id}`}
                    className="inline-flex rounded-xl border border-sky-400/40 bg-sky-950/40 px-4 py-2.5 text-sm font-semibold text-sky-100"
                  >
                    Open repair status
                  </Link>
                ) : row.download_ready && row.download_url ? (
                  <a
                    href={`${API}${row.download_url}`}
                    className="inline-flex rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
                  >
                    Download ZIP
                  </a>
                ) : generating ? (
                  <button
                    type="button"
                    disabled
                    className="inline-flex cursor-wait rounded-xl border border-amber-500/40 bg-amber-950/30 px-4 py-2.5 text-sm font-semibold text-amber-100/90"
                  >
                    generating...
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled
                    className="inline-flex cursor-not-allowed rounded-xl border border-white/10 px-4 py-2.5 text-sm font-semibold text-zinc-500"
                  >
                    Download ZIP
                  </button>
                )}
                <Link
                  href={`/order/status/${row.order_id}`}
                  className="inline-flex rounded-xl border border-white/15 px-4 py-2.5 text-sm text-white hover:bg-white/5"
                >
                  Order details
                </Link>
              </div>
            </li>
          );
        })}
      </ul>
    </ClientWorkspaceShell>
  );
}
