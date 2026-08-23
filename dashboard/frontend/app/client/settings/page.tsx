"use client";

import Link from "next/link";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";

const FUTURE_SECTIONS = [
  "Unternehmensdaten",
  "Profil",
  "Benutzer & Rollen",
  "Benachrichtigungen",
  "Integrationen",
  "Sicherheit",
] as const;

export default function ClientSettingsPage() {
  return (
    <ClientWorkspaceShell
      title="Einstellungen"
      subtitle="Account- und Unternehmenssteuerung — wird schrittweise freigeschaltet."
    >
      <div className="rounded-3xl border border-dashed border-amber-400/30 bg-amber-500/[0.06] p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-300/90">
          Settings — Coming Soon
        </p>
        <h2 className="mt-3 text-xl font-semibold text-white">Einstellungen</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
          Dieser Bereich ist noch nicht aktiv. Es gibt derzeit keine speichernden
          Formulare — Änderungen am Projekt laufen über Website Admin, Store Admin
          und Virtus AI in Ihren gekauften Produkten.
        </p>
        <p className="mt-5 text-sm font-medium text-zinc-300">
          Geplant in Einstellungen:
        </p>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {FUTURE_SECTIONS.map((item) => (
            <li
              key={item}
              className="rounded-xl border border-white/8 bg-black/25 px-3 py-2.5 text-sm text-zinc-400"
            >
              {item}
              <span className="ml-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-600">
                · Soon
              </span>
            </li>
          ))}
        </ul>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/client"
            className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500"
          >
            Zur Übersicht
          </Link>
          <Link
            href="/client/support"
            className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
          >
            Support kontaktieren
          </Link>
        </div>
      </div>
    </ClientWorkspaceShell>
  );
}
