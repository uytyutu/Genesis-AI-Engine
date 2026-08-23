"use client";

import { useMemo, useState } from "react";
import { clientAuthHeaders } from "../lib/clientAuth";
import { formatApiDetail } from "../lib/formatApiError";
import { publicApiBase } from "../lib/publicApiBase";

const API = publicApiBase();

const HINTS: Record<string, string> = {
  dhl: "DHL Geschäftskunden API — billing number + API user/password (or mock).",
  dpd: "DPD Business API credentials for DE/AT.",
  gls: "GLS API client id / secret for BusinessParcel.",
  hermes: "Hermes / Evri merchant API key.",
  ups: "UPS Developer Kit client id + secret.",
  fedex: "FedEx Web Services account + API key.",
};

type Props = {
  orderId: string;
  providerId: string;
  dark?: boolean;
  onDone?: () => void;
  onCancel?: () => void;
};

export function StoreAdminShippingPanel({
  orderId,
  providerId,
  dark = true,
  onDone,
  onCancel,
}: Props) {
  const [accountName, setAccountName] = useState("");
  const [apiUser, setApiUser] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiPassword, setApiPassword] = useState("");
  const [billingNumber, setBillingNumber] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vectorHint, setVectorHint] = useState<string | null>(null);
  const [services, setServices] = useState<{ id: string; label: string }[]>([]);

  const label = useMemo(
    () => providerId.toUpperCase(),
    [providerId],
  );

  const inputCls = dark
    ? "w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm text-white outline-none"
    : "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none";

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/integrations/${providerId}/shipping-connect`,
        {
          method: "POST",
          headers: { ...clientAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            account_name: accountName || undefined,
            api_user: apiUser || undefined,
            api_key: apiKey || undefined,
            api_password: apiPassword || undefined,
            billing_number: billingNumber || undefined,
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiDetail(body.detail) || "shipping_connect_failed");
      setServices(
        ((body.services || []) as { id: string; label: string }[]).map((s) => ({
          id: s.id,
          label: s.label,
        })),
      );
      setVectorHint(body.vector_hint?.message || `✅ ${label} подключён.`);
      onDone?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`space-y-3 rounded-2xl border p-4 ${
        dark ? "border-emerald-500/25 bg-emerald-950/15" : "border-emerald-200 bg-emerald-50"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold">Connect {label}</h4>
          <p className={`mt-0.5 text-[11px] ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            {HINTS[providerId] || "Merchant carrier API — connection is tested on save."}
          </p>
        </div>
        {onCancel ? (
          <button
            type="button"
            className={`text-xs ${dark ? "text-zinc-400" : "text-slate-500"}`}
            onClick={onCancel}
          >
            Cancel
          </button>
        ) : null}
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className={`text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          Account name
          <input
            className={`mt-1 ${inputCls}`}
            value={accountName}
            placeholder={`${label} Business`}
            onChange={(e) => setAccountName(e.target.value)}
          />
        </label>
        <label className={`text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          Billing / Customer number
          <input
            className={`mt-1 ${inputCls}`}
            value={billingNumber}
            onChange={(e) => setBillingNumber(e.target.value)}
          />
        </label>
        <label className={`text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          API user
          <input
            className={`mt-1 ${inputCls}`}
            value={apiUser}
            onChange={(e) => setApiUser(e.target.value)}
          />
        </label>
        <label className={`text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          API key
          <input
            className={`mt-1 ${inputCls}`}
            type="password"
            value={apiKey}
            placeholder="mock or live key"
            onChange={(e) => setApiKey(e.target.value)}
          />
        </label>
        <label className={`text-xs sm:col-span-2 ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          API password
          <input
            className={`mt-1 ${inputCls}`}
            type="password"
            value={apiPassword}
            onChange={(e) => setApiPassword(e.target.value)}
          />
        </label>
      </div>

      {services.length > 0 ? (
        <ul className={`text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
          {services.map((s) => (
            <li key={s.id}>· {s.label}</li>
          ))}
        </ul>
      ) : null}

      {vectorHint ? (
        <p className="text-xs text-emerald-300">{vectorHint}</p>
      ) : null}
      {error ? (
        <p className="text-xs text-rose-400" role="alert">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        disabled={busy}
        className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${
          dark ? "bg-emerald-500/90 text-black" : "bg-emerald-700 text-white"
        }`}
        onClick={() => void save()}
      >
        {busy ? "Connecting…" : "Connect & Test"}
      </button>
    </div>
  );
}
