"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { BccPanel, BccSectionHeader } from "../../lib/clientUi";

const BUSINESS_SECTIONS: {
  title: string;
  hint: string;
  href?: string;
  soon?: boolean;
}[] = [
  {
    title: "Unternehmensprofil",
    hint: "Firmenname, Adresse, Telefon, E-Mail — über Onboarding / Website Admin",
    href: "/client/onboarding",
  },
  {
    title: "Branding",
    hint: "Logo, Farben, Schriften — in gekauften Produkten (Website / Shop Admin)",
    href: "/client/site",
  },
  {
    title: "Mitarbeiter",
    hint: "Benutzer, Rollen und Rechte im Workspace",
    soon: true,
  },
  {
    title: "Domains",
    hint: "Eigene Domain, DNS, SSL — Coming Soon",
    soon: true,
  },
  {
    title: "Integrationen",
    hint: "Google, Analytics, WhatsApp, Telegram, Stripe — Coming Soon",
    soon: true,
  },
  {
    title: "AI & Kanäle",
    hint: "KI-Mitarbeiter, Inbox, Telegram",
    href: "/client/bots",
  },
  {
    title: "Rechnungen & Zahlungen",
    hint: "Zahlungsverlauf, aktive Services — Stripe Portal folgt",
    href: "/client/billing",
  },
];

export default function ClientSettingsPage() {
  return (
    <ClientWorkspaceShell
      title="Business"
      subtitle="Business-Einstellungen — echte Wege oder Coming Soon, keine Scheinformulare."
    >
      <BccPanel className="mb-6 border-dashed border-violet-400/25 bg-violet-500/[0.05] p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300/90">
          Business Control
        </p>
        <h2 className="mt-3 text-xl font-semibold text-white">
          Professionelle Unternehmenssteuerung
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
          Zentrale Editoren für Profil, Rollen und Integrationen folgen. Bis dahin:
          Änderungen an Website, Shop und AI über die Admin-Bereiche Ihrer aktiven
          Produkte — oder Coming Soon, wenn der Modulweg noch nicht lieferbar ist.
        </p>
      </BccPanel>

      <BccSectionHeader title="Bereiche" />
      <ul className="mt-3 grid gap-2 sm:grid-cols-2">
        {BUSINESS_SECTIONS.map((item) => {
          const inner = (
            <>
              <span className="block text-sm font-medium text-zinc-200">
                {item.title}
                {item.soon || !item.href ? (
                  <span className="ml-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-600">
                    · Coming Soon
                  </span>
                ) : null}
              </span>
              <span className="mt-1 block text-xs text-zinc-500">{item.hint}</span>
            </>
          );
          return (
            <li key={item.title}>
              {item.href && !item.soon ? (
                <Link
                  href={item.href}
                  className="block rounded-xl border border-white/8 bg-black/25 px-3 py-3 transition hover:border-violet-400/35"
                >
                  {inner}
                </Link>
              ) : (
                <div className="rounded-xl border border-dashed border-white/8 bg-black/20 px-3 py-3">
                  {inner}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          href="/client"
          className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500"
        >
          Zur Übersicht
        </Link>
        <Link
          href="/client/products"
          className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
        >
          Meine Produkte
        </Link>
        <Link
          href="/client/support"
          className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
        >
          Support
        </Link>
      </div>
    </ClientWorkspaceShell>
  );
}
