"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { PortalApiError, portalFetch } from "../../lib/portalApi";

type LicenseRow = {
  license_id?: string;
  product_id?: string;
  status?: string;
  display_name?: string;
};

export default function ClientLicensesPage() {
  const router = useRouter();
  const [rows, setRows] = useState<LicenseRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setRows(await portalFetch<LicenseRow[]>("/portal/licenses"));
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
      title="Licenses"
      subtitle="Proof of ownership for activated products."
    >
      {error ? <p className="mb-4 text-sm text-rose-200">{error}</p> : null}
      {rows === null ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : rows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
          <p>You have no licenses yet.</p>
          <p className="mt-2">
            After your first purchase or activation, licenses appear here.
          </p>
          <Link
            href="/client/products"
            className="mt-4 inline-flex text-emerald-300 hover:underline"
          >
            Go to My Products →
          </Link>
        </div>
      ) : (
        <ul className="space-y-2">
          {rows.map((row, i) => (
            <li
              key={row.license_id || String(i)}
              className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-zinc-200"
            >
              {row.display_name || row.product_id || row.license_id || "License"}
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
