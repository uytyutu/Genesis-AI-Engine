"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { CONTACT_EMAIL } from "../../lib/siteConfig";
import { ASSISTANT_NAME } from "../../lib/publicBrand";

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
            Payment, ZIP delivery, hosting access, corrections — write to humans:
          </p>
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
