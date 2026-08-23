"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { CONTACT_EMAIL } from "../../lib/siteConfig";
import { publicApiBase } from "../../lib/publicApiBase";
import { getClientToken, clientAuthHeaders } from "../../lib/clientAuth";

function BusinessIdHint() {
  const [businessId, setBusinessId] = useState<string | null>(null);

  useEffect(() => {
    const token = getClientToken();
    if (!token) return;
    const api = publicApiBase();
    fetch(`${api}/api/client/me`, {
      headers: { ...clientAuthHeaders() },
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
        Business ID erscheint nach Anmeldung im Kundenkonto.
      </p>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm">
      <span className="text-zinc-500">Business ID</span>
      <code className="font-mono font-semibold text-zinc-200">{businessId}</code>
      <button
        type="button"
        className="rounded-lg border border-white/15 px-2 py-1 text-xs hover:bg-white/5"
        onClick={() => void navigator.clipboard.writeText(businessId)}
      >
        Kopieren
      </button>
    </div>
  );
}

export default function ClientSupportPage() {
  return (
    <ClientWorkspaceShell
      title="Support"
      subtitle="Persönlicher Kontakt — kein Ticket-System in Gen1."
    >
      <div className="space-y-4">
        <section className="rounded-2xl border border-dashed border-amber-400/25 bg-amber-500/[0.05] p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-300/85">
            Support · Coming Soon
          </p>
          <h2 className="mt-2 text-base font-semibold text-white">Ticket-System</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Ein Support-Postfach mit Ticket-Status ist in Gen1 noch nicht aktiv.
            Wir bauen es ein — bis dahin erreichen Sie uns direkt per E-Mail.
          </p>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-base font-semibold text-white">Kontakt aufnehmen</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Zahlung, ZIP-Lieferung, Hosting-Zugang, Korrekturen — schreiben Sie uns.
            Bitte Business ID angeben, damit wir Ihr Konto sofort finden.
          </p>
          <BusinessIdHint />
          <a
            href={`mailto:${CONTACT_EMAIL}?subject=Virtus%20Core%20Support`}
            className="mt-4 inline-flex min-h-[44px] items-center rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-500"
          >
            E-Mail an Support · {CONTACT_EMAIL}
          </a>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <h2 className="text-base font-semibold text-white">Hilfe im Workspace</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Für Website-, Shop- und AI-Mitarbeiter-Fragen nutzen Sie die Admin-Bereiche
            Ihrer gekauften Produkte — dort sind verfügbare Funktionen und Status sichtbar.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href="/client/site"
              className="rounded-xl border border-white/15 px-3 py-2 text-sm text-zinc-200 hover:bg-white/5"
            >
              Website
            </Link>
            <Link
              href="/client/bots"
              className="rounded-xl border border-white/15 px-3 py-2 text-sm text-zinc-200 hover:bg-white/5"
            >
              KI-Mitarbeiter
            </Link>
            <Link
              href="/client/orders"
              className="rounded-xl border border-white/15 px-3 py-2 text-sm text-zinc-200 hover:bg-white/5"
            >
              Bestellungen
            </Link>
          </div>
        </section>
      </div>
    </ClientWorkspaceShell>
  );
}
