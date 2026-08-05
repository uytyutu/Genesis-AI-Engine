"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type CustomerRow = {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  address_count?: number;
  wishlist_count?: number;
  order_count?: number;
  created_at?: string;
};

type Props = {
  orderId: string;
  dark?: boolean;
};

export function StoreAdminCustomers({ orderId, dark = true }: Props) {
  const [rows, setRows] = useState<CustomerRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const card = dark
    ? "border-white/10 bg-white/[0.03]"
    : "border-slate-200 bg-white/80 shadow-sm";
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/customers`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load customers");
      }
      setRows((body.customers || []) as CustomerRow[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-5">
      <div className={`rounded-3xl border p-5 sm:p-6 ${card}`}>
        <p
          className={`text-xs font-semibold uppercase tracking-[0.2em] ${
            dark ? "text-emerald-300/70" : "text-emerald-700"
          }`}
        >
          Customers
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          Shop buyers
        </h2>
        <p className={`mt-1 text-sm ${muted}`}>
          Store Customer Accounts — completely separate from Virtus Core Client
          Workspace. Checkout arrives in Commerce (R3.3).
        </p>
      </div>

      {error ? (
        <p className="text-sm text-rose-400" role="alert">
          {error}
        </p>
      ) : null}

      <div className={`overflow-hidden rounded-3xl border ${card}`}>
        <table className="min-w-full text-left text-sm">
          <thead
            className={`border-b text-xs uppercase tracking-wider ${
              dark
                ? "border-white/10 text-zinc-500"
                : "border-slate-200 text-slate-500"
            }`}
          >
            <tr>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Addresses</th>
              <th className="px-4 py-3">Wishlist</th>
              <th className="px-4 py-3">Orders</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className={`px-4 py-8 ${muted}`}>
                  Loading…
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={4} className={`px-4 py-10 text-center ${muted}`}>
                  No shop customers yet. Buyers register on the live storefront
                  Account page.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr
                  key={r.id}
                  className={`border-t ${
                    dark ? "border-white/5" : "border-slate-100"
                  }`}
                >
                  <td className="px-4 py-3">
                    <p className="font-medium">
                      {[r.first_name, r.last_name].filter(Boolean).join(" ") ||
                        "—"}
                    </p>
                    <p className={`text-xs ${muted}`}>{r.email}</p>
                  </td>
                  <td className="px-4 py-3">{r.address_count ?? 0}</td>
                  <td className="px-4 py-3">{r.wishlist_count ?? 0}</td>
                  <td className="px-4 py-3">{r.order_count ?? 0}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
