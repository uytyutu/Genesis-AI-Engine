"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { getClientToken } from "../../lib/clientAuth";
import { BccPanel, BccSectionHeader } from "../../lib/clientUi";

const API = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type BusinessProfile = {
  company_name?: string;
  niche?: string;
  description?: string;
  language?: string;
  market?: string;
  contacts?: {
    phone?: string;
    email?: string;
    whatsapp?: string;
    website?: string;
  };
  address?: {
    street?: string;
    city?: string;
    postal_code?: string;
    country?: string;
  };
  services?: { name?: string; description?: string; price_hint?: string }[];
  socials?: Record<string, unknown>;
  media?: { logo_path?: string };
  source?: string;
  updated_at?: string;
};

function token(): string {
  return getClientToken() || "";
}

export default function ClientBusinessProfilePage() {
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasProfile, setHasProfile] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [profile, setProfile] = useState<BusinessProfile | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError(null);
      try {
        const t = token();
        if (!t) {
          setError("Bitte anmelden, um Ihr Business Profile zu sehen.");
          return;
        }
        const res = await fetch(`${API}/api/client/business-profile`, {
          cache: "no-store",
          headers: { Authorization: `Bearer ${t}` },
        });
        const body = await res.json().catch(() => null);
        if (!res.ok) {
          throw new Error(
            typeof body?.detail === "string" ? body.detail : "Profil konnte nicht geladen werden",
          );
        }
        if (cancelled) return;
        setHasProfile(Boolean(body?.has_profile));
        setNote(typeof body?.note === "string" ? body.note : null);
        setProfile(
          body?.has_profile && body?.profile && typeof body.profile === "object"
            ? (body.profile as BusinessProfile)
            : null,
        );
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Fehler");
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const services = profile?.services || [];
  const socialEntries = Object.entries(profile?.socials || {}).filter(
    ([k, v]) => k !== "other" && typeof v === "string" && v.trim(),
  );

  return (
    <ClientWorkspaceShell
      title="Business Profile"
      subtitle="Einmal erfasst — für Website, Factory und spätere Produkte. Bearbeiten folgt (Slice 4)."
    >
      <BccPanel className="mb-6 border-white/10 bg-black/25 p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
          SSOT · read-only
        </p>
        <h2 className="mt-2 text-xl font-semibold text-white">Unternehmensprofil</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
          Diese Daten kommen nur aus dem Business Profile — nicht aus einer zweiten
          «Gift»- oder Order-Kopie. Write-back und Giveaway folgen in späteren Schritten.
        </p>
      </BccPanel>

      {busy ? <p className="text-sm text-zinc-500">Laden…</p> : null}
      {error ? (
        <p className="rounded-xl border border-rose-500/30 bg-rose-950/20 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}

      {!busy && !error && !hasProfile ? (
        <BccPanel className="border-dashed border-amber-500/25 bg-amber-950/10 p-6">
          <BccSectionHeader title="Noch kein Profil" />
          <p className="mt-2 text-sm text-zinc-400">
            {note ||
              "Business Profile ist noch nicht ausgefüllt. Virtus legt keine zweite Entität an — bei Bestellung oder Giveaway wird dieses eine Profil befüllt."}
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/client/products"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              Meine Produkte
            </Link>
            <Link
              href="/client/settings"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              Business-Einstellungen
            </Link>
          </div>
        </BccPanel>
      ) : null}

      {!busy && !error && hasProfile && profile ? (
        <div className="space-y-4">
          <BccPanel className="p-6">
            <h3 className="text-lg font-semibold text-white">
              {profile.company_name || "Unternehmen"}
            </h3>
            <p className="mt-1 text-sm text-zinc-400">
              {profile.niche || "—"} · {profile.market || "—"} / {profile.language || "—"}
            </p>
            {profile.description ? (
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
                {profile.description}
              </p>
            ) : null}
            {profile.updated_at ? (
              <p className="mt-3 text-[11px] text-zinc-600">
                Aktualisiert {profile.updated_at.slice(0, 19)}
                {profile.source ? ` · Quelle ${profile.source}` : ""}
              </p>
            ) : null}
          </BccPanel>

          <BccPanel className="p-6">
            <BccSectionHeader title="Kontakt & Adresse" />
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-[11px] uppercase tracking-wide text-zinc-500">Telefon</dt>
                <dd className="text-zinc-200">{profile.contacts?.phone || "—"}</dd>
              </div>
              <div>
                <dt className="text-[11px] uppercase tracking-wide text-zinc-500">WhatsApp</dt>
                <dd className="text-zinc-200">{profile.contacts?.whatsapp || "—"}</dd>
              </div>
              <div>
                <dt className="text-[11px] uppercase tracking-wide text-zinc-500">E-Mail</dt>
                <dd className="text-zinc-200">{profile.contacts?.email || "—"}</dd>
              </div>
              <div>
                <dt className="text-[11px] uppercase tracking-wide text-zinc-500">Website</dt>
                <dd className="text-zinc-200">{profile.contacts?.website || "—"}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-[11px] uppercase tracking-wide text-zinc-500">Adresse</dt>
                <dd className="text-zinc-200">
                  {[
                    profile.address?.street,
                    [profile.address?.postal_code, profile.address?.city].filter(Boolean).join(" "),
                    profile.address?.country,
                  ]
                    .filter(Boolean)
                    .join(", ") || "—"}
                </dd>
              </div>
            </dl>
          </BccPanel>

          <BccPanel className="p-6">
            <BccSectionHeader title="Leistungen" />
            {services.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">Noch keine Leistungen hinterlegt.</p>
            ) : (
              <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                {services.map((s, i) => (
                  <li key={`${s.name}-${i}`}>
                    <span className="font-medium text-zinc-100">{s.name}</span>
                    {s.price_hint ? (
                      <span className="text-zinc-500"> · {s.price_hint}</span>
                    ) : null}
                    {s.description ? (
                      <span className="mt-0.5 block text-xs text-zinc-500">{s.description}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </BccPanel>

          {socialEntries.length > 0 ? (
            <BccPanel className="p-6">
              <BccSectionHeader title="Social" />
              <ul className="mt-2 space-y-1 text-sm text-zinc-300">
                {socialEntries.map(([k, v]) => (
                  <li key={k}>
                    <span className="text-zinc-500">{k}: </span>
                    {String(v)}
                  </li>
                ))}
              </ul>
            </BccPanel>
          ) : null}

          <p className="text-xs text-zinc-600">
            Bearbeitung im Client Workspace folgt — Slice 4 (write-back). Factory nutzt dieses
            Profil ab Slice 3.
          </p>
        </div>
      ) : null}
    </ClientWorkspaceShell>
  );
}
