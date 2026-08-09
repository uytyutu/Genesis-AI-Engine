"use client";

import { useCallback, useEffect, useState } from "react";
import { clientAuthHeaders } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

type Profile = {
  company_name?: string | null;
  phone_country_code?: string | null;
  phone_primary?: string | null;
  phone_secondary?: string | null;
  whatsapp?: string | null;
  telegram?: string | null;
  email_support?: string | null;
  email_orders?: string | null;
  hours?: string | null;
  address?: {
    street?: string | null;
    postal_code?: string | null;
    city?: string | null;
    country?: string | null;
  };
  social_links?: Record<string, string | null | undefined>;
};

type Props = {
  orderId: string;
  dark?: boolean;
};

const COUNTRIES = ["DE", "AT", "CH", "NL", "BE", "FR", "PL", "IT", "ES", "GB", "US", "UA"];

export function StoreAdminBusinessProfile({ orderId, dark = true }: Props) {
  const [profile, setProfile] = useState<Profile>({});
  const [derived, setDerived] = useState<Record<string, string | null>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const inputCls = dark
    ? "w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white outline-none"
    : "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none";
  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/business-profile`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "load_failed");
      setProfile((body.profile || {}) as Profile);
      setDerived((body.derived || {}) as Record<string, string | null>);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  function setField<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile((p) => ({ ...p, [key]: value }));
    setSaved(false);
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/business-profile`,
        {
          method: "PATCH",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify(profile),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "save_failed");
      setProfile((body.profile || {}) as Profile);
      setDerived((body.derived || {}) as Record<string, string | null>);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const addr = profile.address || {};
  const social = profile.social_links || {};

  return (
    <section
      className={`space-y-3 rounded-2xl border p-4 ${
        dark ? "border-white/10 bg-black/20" : "border-slate-200 bg-white"
      }`}
    >
      <div>
        <h3 className="text-lg font-semibold tracking-tight">Contact & Communication</h3>
        <p className={`mt-1 text-xs ${muted}`}>
          One Business Profile — website, store, emails, PDF, and forms stay in sync.
        </p>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-xs sm:col-span-2">
          Company name
          <input
            className={inputCls}
            value={profile.company_name || ""}
            onChange={(e) => setField("company_name", e.target.value)}
          />
        </label>
        <label className="text-xs">
          Country code
          <select
            className={inputCls}
            value={profile.phone_country_code || "DE"}
            onChange={(e) => setField("phone_country_code", e.target.value)}
          >
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs">
          Primary phone
          <input
            className={inputCls}
            value={profile.phone_primary || ""}
            onChange={(e) => setField("phone_primary", e.target.value)}
            placeholder="030 123456"
          />
        </label>
        <label className="text-xs">
          Secondary phone
          <input
            className={inputCls}
            value={profile.phone_secondary || ""}
            onChange={(e) => setField("phone_secondary", e.target.value)}
          />
        </label>
        <label className="text-xs">
          WhatsApp
          <input
            className={inputCls}
            value={profile.whatsapp || ""}
            onChange={(e) => setField("whatsapp", e.target.value)}
            placeholder="same as phone or +49…"
          />
        </label>
        <label className="text-xs">
          Telegram
          <input
            className={inputCls}
            value={profile.telegram || ""}
            onChange={(e) => setField("telegram", e.target.value)}
            placeholder="@handle"
          />
        </label>
        <label className="text-xs">
          Support email
          <input
            className={inputCls}
            value={profile.email_support || ""}
            onChange={(e) => setField("email_support", e.target.value)}
          />
        </label>
        <label className="text-xs">
          Orders email
          <input
            className={inputCls}
            value={profile.email_orders || ""}
            onChange={(e) => setField("email_orders", e.target.value)}
          />
        </label>
        <label className="text-xs sm:col-span-2">
          Street
          <input
            className={inputCls}
            value={addr.street || ""}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                address: { ...(p.address || {}), street: e.target.value },
              }))
            }
          />
        </label>
        <label className="text-xs">
          Postal code
          <input
            className={inputCls}
            value={addr.postal_code || ""}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                address: { ...(p.address || {}), postal_code: e.target.value },
              }))
            }
          />
        </label>
        <label className="text-xs">
          City
          <input
            className={inputCls}
            value={addr.city || ""}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                address: { ...(p.address || {}), city: e.target.value },
              }))
            }
          />
        </label>
        <label className="text-xs sm:col-span-2">
          Hours
          <input
            className={inputCls}
            value={profile.hours || ""}
            onChange={(e) => setField("hours", e.target.value)}
            placeholder="Mo–Fr 9:00–18:00"
          />
        </label>
        <label className="text-xs">
          Instagram
          <input
            className={inputCls}
            value={social.instagram || ""}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                social_links: { ...(p.social_links || {}), instagram: e.target.value },
              }))
            }
          />
        </label>
        <label className="text-xs">
          Facebook
          <input
            className={inputCls}
            value={social.facebook || ""}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                social_links: { ...(p.social_links || {}), facebook: e.target.value },
              }))
            }
          />
        </label>
      </div>

      {(derived.tel_primary || derived.whatsapp_url) && (
        <p className={`text-[11px] ${muted}`}>
          Links:{" "}
          {derived.tel_primary ? (
            <a className="underline" href={derived.tel_primary}>
              {derived.phone_primary_display || "tel"}
            </a>
          ) : null}
          {derived.whatsapp_url ? (
            <>
              {" · "}
              <a className="underline" href={derived.whatsapp_url} target="_blank" rel="noreferrer">
                WhatsApp
              </a>
            </>
          ) : null}
        </p>
      )}

      {error ? <p className="text-xs text-rose-400">{error}</p> : null}
      {saved ? (
        <p className={`text-xs ${dark ? "text-emerald-300" : "text-emerald-700"}`}>
          Saved — applies across Website, Store, Email, PDF, and forms.
        </p>
      ) : null}

      <button
        type="button"
        disabled={saving}
        onClick={() => void save()}
        className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${
          dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
        }`}
      >
        {saving ? "Saving…" : "Save contacts"}
      </button>
    </section>
  );
}
