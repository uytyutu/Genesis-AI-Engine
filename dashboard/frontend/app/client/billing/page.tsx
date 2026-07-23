"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { PortalApiError, portalFetch } from "../../lib/portalApi";

type BillingRow = {
  transaction_id?: string;
  amount?: number | string;
  currency?: string;
  status?: string;
  created_at?: string;
  product_id?: string;
};

export default function ClientBillingPage() {
  const router = useRouter();
  const [rows, setRows] = useState<BillingRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await portalFetch<BillingRow[]>("/portal/billing"));
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
      title="Billing"
      subtitle="Invoices and payment history for your account."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {rows === null ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>You have no invoices yet.</p>
          <p className="mt-2">
            After your first purchase, billing history appears here.
          </p>
          <Link
            href="/order"
            className="mt-4 inline-flex text-emerald-300 hover:underline"
          >
            Order Landing Website →
          </Link>
        </div>
      ) : (
        <ul className="space-y-2">
          {rows.map((row, i) => (
            <li
              key={row.transaction_id || String(i)}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-zinc-200"
            >
              {row.product_id || row.transaction_id || "Transaction"}
              {row.amount != null ? (
                <span className="text-zinc-400">
                  {" "}
                  · {String(row.amount)} {row.currency || ""}
                </span>
              ) : null}
              {row.status ? (
                <span className="text-zinc-500"> · {row.status}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </ClientWorkspaceShell>
  );
}
