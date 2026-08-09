"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { CONTACT_EMAIL } from "../../lib/siteConfig";
import { ASSISTANT_NAME } from "../../lib/publicBrand";
import { publicApiBase } from "../../lib/publicApiBase";
import { getClientToken } from "../../lib/clientAuth";

function BusinessIdHint() {
  const [businessId, setBusinessId] = useState<string | null>(null);

  useEffect(() => {
    const token = getClientToken();
    if (!token) return;
    const api = publicApiBase();
    fetch(`${api}/api/client/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        const id = body?.business_id;
        if (typeof id === "string" && id.startsWith("VC-")) setBusinessId(id);
      })
      .catch(() => undefined);
  }, []);

  if (!businessId) {
    return (
      <p className="mt-3 text-xs text-zinc-500">
        Business ID появляется после входа в кабинет.
      </p>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-emerald-500/25 bg-emerald-950/20 px-3 py-2 text-sm">
      <span className="text-genesis-muted">Business ID</span>
      <code className="font-mono font-semibold text-emerald-100">{businessId}</code>
      <button
        type="button"
        className="rounded-lg border border-white/15 px-2 py-1 text-xs hover:bg-white/5"
        onClick={() => void navigator.clipboard.writeText(businessId)}
      >
        Copy
      </button>
    </div>
  );
}

export default function ClientSupportPage() {
  return (
    <ClientWorkspaceShell
      title="Support"
      subtitle="Ask your AI Business Employee first — then contact humans if needed."
    >
      <div className="space-y-4">
        <section className="rounded-2xl border border-sky-400/25 bg-sky-500/[0.07] p-5">
          <h2 className="text-base font-semibold text-white">
            Ask {ASSISTANT_NAME} first
          </h2>
          <p className="mt-2 text-sm text-zinc-300">
            Most questions about your products, conversations, and next steps —
            {ASSISTANT_NAME} can answer inside your workspace.
          </p>
          <Link
            href="/projects/chatbot"
            className="mt-4 inline-flex rounded-xl bg-sky-400 px-4 py-2.5 text-sm font-semibold text-black hover:brightness-110"
          >
            Ask {ASSISTANT_NAME} →
          </Link>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-base font-semibold text-white">Contact Support</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Payment, ZIP delivery, hosting access, corrections — write to humans.
            Include your Business ID so we find your account instantly.
          </p>
          <BusinessIdHint />
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="mt-3 inline-flex rounded-xl border border-white/15 px-4 py-2 text-sm text-white hover:bg-white/5"
          >
            Contact Support · {CONTACT_EMAIL}
          </a>
        </section>
      </div>
    </ClientWorkspaceShell>
  );
}
