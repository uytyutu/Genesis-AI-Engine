"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type ShopOrder = {
  id: string;
  status?: string;
  total_eur?: number;
  created_at?: string;
  buyer_email?: string;
  payment_method?: { label?: string };
  shipping_method?: { label?: string; carrier?: string; id?: string };
  shipment?: {
    id?: string;
    tracking_number?: string;
    tracking_url?: string;
    status?: string;
    carrier?: string;
    service_label?: string;
  };
  items?: { title?: string; qty?: number }[];
};

const PIPELINE = ["Order", "Shipment", "Tracking Number", "Delivered"];

function pipelineStep(o: ShopOrder): number {
  if (o.status === "delivered" || o.shipment?.status === "delivered") return 3;
  if (o.shipment?.tracking_number) return 2;
  if (o.shipment?.id || o.status === "shipped") return 1;
  return 0;
}

export function StoreAdminOrders({
  orderId,
  dark = true,
}: {
  orderId: string;
  dark?: boolean;
}) {
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/orders`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load orders");
      }
      setOrders((body.orders || []) as ShopOrder[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function createShipment(shopOrderId: string) {
    setBusyId(shopOrderId);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/shipping/shipments`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ shop_order_id: shopOrderId }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "create_shipment_failed");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  async function advanceTrack(tracking?: string) {
    if (!tracking) return;
    setBusyId(tracking);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/shipping/track`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ tracking_number: tracking, advance: true }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "track_failed");
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Orders</h2>
        <p className={`mt-1 text-sm ${muted}`}>
          Order → Shipment → Tracking Number → Delivered
        </p>
      </div>
      {error ? (
        <p className="text-sm text-rose-400" role="alert">
          {error}
        </p>
      ) : null}
      {orders.length === 0 ? (
        <p className={`text-sm ${muted}`}>No shop orders yet.</p>
      ) : (
        <ul className="space-y-2">
          {orders.map((o) => {
            const step = pipelineStep(o);
            const carrier = o.shipment?.carrier || o.shipping_method?.carrier;
            const canShip =
              Boolean(carrier) &&
              !["pickup", "local_delivery"].includes(String(carrier)) &&
              !o.shipment?.tracking_number;
            return (
              <li
                key={o.id}
                className={`rounded-2xl border px-4 py-3 text-sm ${
                  dark ? "border-white/10 bg-black/20" : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <strong>{o.id}</strong>
                  <span>{Number(o.total_eur || 0).toFixed(2)} €</span>
                </div>
                <p className={`mt-1 text-xs ${muted}`}>
                  {o.status} · {o.buyer_email || "—"} ·{" "}
                  {o.payment_method?.label || "—"} · {o.shipping_method?.label || "—"}
                </p>
                {o.shipment?.tracking_number ? (
                  <p className={`mt-1 text-xs ${dark ? "text-emerald-300" : "text-emerald-700"}`}>
                    {(o.shipment.carrier || "").toUpperCase()} · {o.shipment.tracking_number} ·{" "}
                    {o.shipment.status}
                    {o.shipment.tracking_url ? (
                      <>
                        {" · "}
                        <a
                          href={o.shipment.tracking_url}
                          target="_blank"
                          rel="noreferrer"
                          className="underline"
                        >
                          Track
                        </a>
                      </>
                    ) : null}
                  </p>
                ) : null}
                <ol className="mt-2 flex flex-wrap gap-1.5 text-[10px] font-semibold uppercase tracking-wide">
                  {PIPELINE.map((label, i) => (
                    <li
                      key={label}
                      className={`rounded-full px-2 py-0.5 ${
                        i <= step
                          ? dark
                            ? "bg-emerald-500/20 text-emerald-200"
                            : "bg-emerald-100 text-emerald-800"
                          : dark
                            ? "bg-white/5 text-zinc-500"
                            : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {label}
                    </li>
                  ))}
                </ol>
                <div className="mt-2 flex flex-wrap gap-2">
                  {canShip ? (
                    <button
                      type="button"
                      disabled={busyId === o.id}
                      className={`rounded-xl px-3 py-1.5 text-xs font-semibold disabled:opacity-50 ${
                        dark
                          ? "bg-emerald-500/90 text-black"
                          : "bg-emerald-700 text-white"
                      }`}
                      onClick={() => void createShipment(o.id)}
                    >
                      Create Shipment
                    </button>
                  ) : null}
                  {o.shipment?.tracking_number && o.shipment.status !== "delivered" ? (
                    <button
                      type="button"
                      disabled={busyId === o.shipment.tracking_number}
                      className={`rounded-xl border px-3 py-1.5 text-xs font-semibold disabled:opacity-50 ${
                        dark ? "border-white/15" : "border-slate-200"
                      }`}
                      onClick={() => void advanceTrack(o.shipment?.tracking_number)}
                    >
                      Advance Track
                    </button>
                  ) : null}
                </div>
                <p className={`mt-1 text-xs ${muted}`}>{o.created_at}</p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
