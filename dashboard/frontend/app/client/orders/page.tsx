"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";

export default function ClientOrdersPage() {
  return (
    <ClientWorkspaceShell
      title="Orders"
      subtitle="Landing checkout and delivery status."
    >
      <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
        <p>Orders from the public checkout live in order history.</p>
        <p className="mt-2">
          After your first paid Landing, you will see status and files there.
          Portal product purchases show under My Products and Billing.
        </p>
        <Link
          href="/order/history"
          className="mt-4 inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-black hover:brightness-110"
        >
          Open order history →
        </Link>
      </div>
    </ClientWorkspaceShell>
  );
}
