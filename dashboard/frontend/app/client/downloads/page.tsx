"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";

export default function ClientDownloadsPage() {
  return (
    <ClientWorkspaceShell
      title="Downloads"
      subtitle="Delivery files for completed Landing orders."
    >
      <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-sm text-zinc-400">
        <p>No downloads listed here yet.</p>
        <p className="mt-2">
          After your first Landing delivery, ZIP archives and publish guides
          appear in order history. This page will list them once linked to your
          account.
        </p>
        <Link
          href="/order/history"
          className="mt-4 inline-flex rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
        >
          Open order history →
        </Link>
      </div>
    </ClientWorkspaceShell>
  );
}
