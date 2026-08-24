"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { PortalApiError, portalFetch } from "../../lib/portalApi";
import { BccPanel, BccSectionHeader } from "../../lib/clientUi";

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
      title="Abrechnung"
      subtitle="Zahlungsverlauf · Self-Service-Portal folgt."
    >
      <BccPanel className="mb-6 border-dashed border-amber-400/25 bg-amber-500/[0.05] p-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-300/85">
          Stripe-Kundenportal — Demnächst
        </p>
        <p className="mt-2 text-sm text-zinc-400">
          Rechnungen herunterladen, Zahlungsmethode ändern und Abos verwalten —
          über das Stripe Customer Portal. Aktuell sehen Sie den echten
          Zahlungsverlauf; Self-Service wird angebunden, sobald produktiv
          freigeschaltet.
        </p>
      </BccPanel>

      <BccPanel className="p-5">
        <BccSectionHeader
          title="Zahlungsverlauf"
          actionHref="/client/orders"
          actionLabel="Bestellungen →"
        />
        {error ? <p className="mt-3 text-sm text-rose-200">{error}</p> : null}
        {rows === null ? (
          <p className="mt-3 text-sm text-zinc-500">Laden…</p>
        ) : rows.length === 0 ? (
          <div className="mt-3 rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
            <p>Noch keine Zahlungen in Ihrem Konto.</p>
            <p className="mt-2">
              Nach dem ersten Kauf erscheint der Verlauf hier — ohne simulierte
              Abo-Steuerung.
            </p>
            <Link
              href="/order?form=1"
              className="mt-4 inline-flex text-violet-300 hover:underline"
            >
              Website bestellen →
            </Link>
          </div>
        ) : (
          <ul className="mt-3 space-y-2">
            {rows.map((row, i) => (
              <li
                key={row.transaction_id || String(i)}
                className="rounded-xl border border-white/10 bg-black/25 px-3 py-3 text-sm text-zinc-200"
              >
                <span className="font-medium text-white">
                  {row.product_id || row.transaction_id || "Transaktion"}
                </span>
                {row.amount != null ? (
                  <span className="text-zinc-400">
                    {" "}
                    · {String(row.amount)} {row.currency || ""}
                  </span>
                ) : null}
                {row.status ? (
                  <span className="text-zinc-500"> · {row.status}</span>
                ) : (
                  <span className="text-zinc-600"> · Unknown</span>
                )}
                {row.created_at ? (
                  <span className="mt-1 block text-xs text-zinc-600">
                    {row.created_at}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </BccPanel>

      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        <Link
          href="/client/downloads"
          className="rounded-xl border border-white/15 px-3 py-2 text-zinc-300 hover:bg-white/5"
        >
          Downloads / ZIP
        </Link>
        <Link
          href="/client/support"
          className="rounded-xl border border-white/15 px-3 py-2 text-zinc-300 hover:bg-white/5"
        >
          Support bei Zahlungsfragen
        </Link>
      </div>
    </ClientWorkspaceShell>
  );
}
