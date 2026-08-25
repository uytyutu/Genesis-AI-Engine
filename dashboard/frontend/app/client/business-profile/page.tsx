"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ClientWorkspaceShell } from "../../components/ClientWorkspaceShell";
import { getClientToken } from "../../lib/clientAuth";
import { BccPanel, BccSectionHeader } from "../../lib/clientUi";
import { getBackendApiBase } from "../../lib/backendApiBase";

const API = getBackendApiBase();

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
  socials?: {
    instagram?: string;
    facebook?: string;
    linkedin?: string;
    tiktok?: string;
    youtube?: string;
  };
  source?: string;
  updated_at?: string;
};

const emptyProfile = (): BusinessProfile => ({
  company_name: "",
  niche: "",
  description: "",
  language: "de",
  market: "DE",
  contacts: { phone: "", email: "", whatsapp: "", website: "" },
  address: { street: "", city: "", postal_code: "", country: "DE" },
  services: [{ name: "" }],
  socials: { instagram: "", facebook: "" },
});

export default function ClientBusinessProfilePage() {
  const [busy, setBusy] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [profile, setProfile] = useState<BusinessProfile>(emptyProfile());
  const [websitesSynced, setWebsitesSynced] = useState<number | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const t = getClientToken();
      if (!t) {
        setError("Bitte anmelden, um Ihr Business Profile zu bearbeiten.");
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
      if (body?.has_profile && body?.profile && typeof body.profile === "object") {
        const p = body.profile as BusinessProfile;
        setProfile({
          ...emptyProfile(),
          ...p,
          contacts: { ...emptyProfile().contacts, ...(p.contacts || {}) },
          address: { ...emptyProfile().address, ...(p.address || {}) },
          socials: { ...emptyProfile().socials, ...(p.socials || {}) },
          services:
            Array.isArray(p.services) && p.services.length > 0
              ? p.services
              : [{ name: "" }],
        });
      } else {
        setProfile(emptyProfile());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    setSaving(true);
    setError(null);
    setSavedMsg(null);
    setWebsitesSynced(null);
    try {
      const t = getClientToken();
      if (!t) throw new Error("Nicht angemeldet");
      const services = (profile.services || [])
        .map((s) => ({
          name: String(s.name || "").trim(),
          description: String(s.description || "").trim(),
          price_hint: String(s.price_hint || "").trim(),
        }))
        .filter((s) => s.name);
      const res = await fetch(`${API}/api/client/business-profile`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${t}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          company_name: profile.company_name,
          niche: profile.niche,
          description: profile.description,
          language: profile.language || "de",
          market: profile.market || "DE",
          contacts: profile.contacts,
          address: profile.address,
          services,
          socials: profile.socials,
        }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        throw new Error(
          typeof body?.detail === "string" ? body.detail : "Speichern fehlgeschlagen",
        );
      }
      if (body?.profile) {
        const p = body.profile as BusinessProfile;
        setProfile({
          ...emptyProfile(),
          ...p,
          contacts: { ...emptyProfile().contacts, ...(p.contacts || {}) },
          address: { ...emptyProfile().address, ...(p.address || {}) },
          socials: { ...emptyProfile().socials, ...(p.socials || {}) },
          services:
            Array.isArray(p.services) && p.services.length > 0
              ? p.services
              : [{ name: "" }],
        });
      }
      setWebsitesSynced(
        typeof body?.websites_synced === "number" ? body.websites_synced : null,
      );
      setSavedMsg(
        "Gespeichert — Business Profile ist die Quelle für Website, Factory und weitere Produkte.",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setSaving(false);
    }
  };

  const inputCls =
    "mt-1 w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm text-white";

  return (
    <ClientWorkspaceShell
      title="Unternehmensprofil"
      subtitle="Einmal erfassen — für Website, Factory und weitere Virtus-Produkte."
    >
      <BccPanel className="mb-6 border-white/10 bg-black/25 p-6 sm:p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
          Business Profile · SSOT
        </p>
        <h2 className="mt-2 text-xl font-semibold text-white">Ihr Unternehmensprofil</h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
          Diese Angaben werden für Ihre Website und weitere Virtus-Produkte verwendet. Änderungen
          hier aktualisieren den zentralen Profil-SSOT — nicht eine zweite Kopie.
        </p>
      </BccPanel>

      {busy ? <p className="text-sm text-zinc-500">Laden…</p> : null}
      {error ? (
        <p className="mb-4 rounded-xl border border-rose-500/30 bg-rose-950/20 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}
      {savedMsg ? (
        <p className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 px-4 py-3 text-sm text-emerald-100">
          {savedMsg}
          {websitesSynced != null ? ` · Website-Kontakte synchronisiert: ${websitesSynced}` : ""}
        </p>
      ) : null}

      {!busy && !error ? (
        <div className="space-y-4">
          <BccPanel className="p-6">
            <BccSectionHeader title="Unternehmen" />
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <label className="block text-xs text-zinc-400 sm:col-span-2">
                Firmenname
                <input
                  className={inputCls}
                  value={profile.company_name || ""}
                  onChange={(e) =>
                    setProfile({ ...profile, company_name: e.target.value })
                  }
                />
              </label>
              <label className="block text-xs text-zinc-400">
                Nische
                <input
                  className={inputCls}
                  value={profile.niche || ""}
                  onChange={(e) => setProfile({ ...profile, niche: e.target.value })}
                  placeholder="z. B. handwerk"
                />
              </label>
              <label className="block text-xs text-zinc-400">
                Markt / Sprache
                <div className="mt-1 flex gap-2">
                  <input
                    className={inputCls + " !mt-0"}
                    value={profile.market || ""}
                    onChange={(e) => setProfile({ ...profile, market: e.target.value })}
                    placeholder="DE"
                  />
                  <input
                    className={inputCls + " !mt-0"}
                    value={profile.language || ""}
                    onChange={(e) => setProfile({ ...profile, language: e.target.value })}
                    placeholder="de"
                  />
                </div>
              </label>
              <label className="block text-xs text-zinc-400 sm:col-span-2">
                Beschreibung
                <textarea
                  className={inputCls + " min-h-[96px]"}
                  value={profile.description || ""}
                  onChange={(e) =>
                    setProfile({ ...profile, description: e.target.value })
                  }
                />
              </label>
            </div>
          </BccPanel>

          <BccPanel className="p-6">
            <BccSectionHeader title="Kontakt & Adresse" />
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {(
                [
                  ["phone", "Telefon"],
                  ["whatsapp", "WhatsApp"],
                  ["email", "E-Mail"],
                  ["website", "Website"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="block text-xs text-zinc-400">
                  {label}
                  <input
                    className={inputCls}
                    value={profile.contacts?.[key] || ""}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        contacts: { ...(profile.contacts || {}), [key]: e.target.value },
                      })
                    }
                  />
                </label>
              ))}
              {(
                [
                  ["street", "Straße"],
                  ["postal_code", "PLZ"],
                  ["city", "Stadt"],
                  ["country", "Land"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="block text-xs text-zinc-400">
                  {label}
                  <input
                    className={inputCls}
                    value={profile.address?.[key] || ""}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        address: { ...(profile.address || {}), [key]: e.target.value },
                      })
                    }
                  />
                </label>
              ))}
            </div>
          </BccPanel>

          <BccPanel className="p-6">
            <BccSectionHeader title="Leistungen" />
            <ul className="mt-3 space-y-2">
              {(profile.services || [{ name: "" }]).map((s, i) => (
                <li key={i}>
                  <input
                    className={inputCls}
                    placeholder="Leistung"
                    value={s.name || ""}
                    onChange={(e) => {
                      const next = [...(profile.services || [])];
                      next[i] = { ...next[i], name: e.target.value };
                      setProfile({ ...profile, services: next });
                    }}
                  />
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="mt-2 text-xs text-sky-300 hover:underline"
              onClick={() =>
                setProfile({
                  ...profile,
                  services: [...(profile.services || []), { name: "" }],
                })
              }
            >
              + Leistung
            </button>
          </BccPanel>

          <BccPanel className="p-6">
            <BccSectionHeader title="Social" />
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {(
                [
                  ["instagram", "Instagram"],
                  ["facebook", "Facebook"],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="block text-xs text-zinc-400">
                  {label}
                  <input
                    className={inputCls}
                    value={profile.socials?.[key] || ""}
                    onChange={(e) =>
                      setProfile({
                        ...profile,
                        socials: { ...(profile.socials || {}), [key]: e.target.value },
                      })
                    }
                  />
                </label>
              ))}
            </div>
          </BccPanel>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={saving}
              onClick={() => void save()}
              className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-50"
            >
              {saving ? "Speichern…" : "Profil speichern"}
            </button>
            <Link
              href="/client/settings"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              Zurück zu Business
            </Link>
            <Link
              href="/client/site"
              className="rounded-xl border border-white/15 px-4 py-2 text-sm text-zinc-300 hover:bg-white/5"
            >
              Website
            </Link>
          </div>
        </div>
      ) : null}
    </ClientWorkspaceShell>
  );
}
