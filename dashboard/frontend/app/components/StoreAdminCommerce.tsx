"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { clientAuthHeaders } from "../../lib/clientAuth";
import { formatApiDetail } from "../../lib/formatApiError";
import { publicApiBase } from "../../lib/publicApiBase";

const API = publicApiBase();

type Conn = { id?: string; label?: string; status?: string; note?: string };

type CommerceSettings = {
  payments?: Record<string, Conn>;
  shipping?: Record<string, Conn>;
  taxes?: Conn;
  currencies?: Conn & { primary?: string };
  email?: Conn;
  invoices?: Conn;
};

type Props = {
  orderId: string;
  dark?: boolean;
  focus?: "overview" | "payments" | "shipping";
};

function StatusPill({
  status,
  dark,
}: {
  status?: string;
  dark: boolean;
}) {
  const connected = status === "connected";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
        connected
          ? dark
            ? "bg-emerald-500/20 text-emerald-200"
            : "bg-emerald-100 text-emerald-800"
          : dark
            ? "bg-amber-500/15 text-amber-200"
            : "bg-amber-50 text-amber-800"
      }`}
    >
      {connected ? "Connected" : "Not connected"}
    </span>
  );
}

function Block({
  title,
  hint,
  dark,
  children,
}: {
  title: string;
  hint?: string;
  dark: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`rounded-3xl border p-5 ${
        dark
          ? "border-white/10 bg-white/[0.03]"
          : "border-slate-200 bg-white/80 shadow-sm"
      }`}
    >
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
        {hint ? (
          <p className={`text-xs ${dark ? "text-zinc-500" : "text-slate-500"}`}>
            {hint}
          </p>
        ) : null}
      </div>
      {children}
    </div>
  );
}

export function StoreAdminCommerce({
  orderId,
  dark = true,
  focus = "overview",
}: Props) {
  const [settings, setSettings] = useState<CommerceSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  const muted = dark ? "text-zinc-500" : "text-slate-500";

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/api/client/stores/${orderId}/admin/commerce`,
        { headers: { ...clientAuthHeaders() }, cache: "no-store" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(formatApiDetail(body.detail) || "Failed to load commerce");
      }
      setSettings((body.settings || {}) as CommerceSettings);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const payments = Object.values(settings?.payments || {});
  const shipping = Object.values(settings?.shipping || {});

  const showPayments = focus === "overview" || focus === "payments";
  const showShipping = focus === "overview" || focus === "shipping";
  const showRest = focus === "overview";

  return (
    <div className="space-y-5">
      <div
        className={`rounded-3xl border p-5 sm:p-6 ${
          dark
            ? "border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-white/[0.03] to-transparent"
            : "border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-amber-50/40 shadow-sm"
        }`}
      >
        <p
          className={`text-xs font-semibold uppercase tracking-[0.2em] ${
            dark ? "text-emerald-300/70" : "text-emerald-700"
          }`}
        >
          Commerce
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          Prepare your shop for selling
        </h2>
        <p className={`mt-1 max-w-2xl text-sm ${muted}`}>
          Payment and shipping connections activate in R3.3. This panel shows
          what will open next — nothing charges buyers yet.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-rose-400" role="alert">
          {error}
        </p>
      ) : null}

      {showPayments ? (
        <Block title="Payments" hint="R3.3.1 · Stripe, PayPal, Klarna, SEPA" dark={dark}>
          <div className="grid gap-3 sm:grid-cols-2">
            {(payments.length
              ? payments
              : [
                  { label: "Stripe Connect" },
                  { label: "PayPal" },
                  { label: "Klarna" },
                  { label: "SEPA" },
                ]
            ).map((p) => (
              <div
                key={p.id || p.label}
                className={`flex items-center justify-between rounded-2xl border px-4 py-3 ${
                  dark ? "border-white/10" : "border-slate-200"
                }`}
              >
                <span className="text-sm font-medium">{p.label}</span>
                <StatusPill status={p.status} dark={dark} />
              </div>
            ))}
          </div>
        </Block>
      ) : null}

      {showShipping ? (
        <Block title="Shipping" hint="R3.3.3 · DHL, Hermes, DPD, UPS" dark={dark}>
          <div className="grid gap-3 sm:grid-cols-2">
            {(shipping.length
              ? shipping
              : [
                  { label: "DHL" },
                  { label: "Hermes" },
                  { label: "DPD" },
                  { label: "UPS" },
                ]
            ).map((p) => (
              <div
                key={p.id || p.label}
                className={`flex items-center justify-between rounded-2xl border px-4 py-3 ${
                  dark ? "border-white/10" : "border-slate-200"
                }`}
              >
                <span className="text-sm font-medium">{p.label}</span>
                <StatusPill status={p.status} dark={dark} />
              </div>
            ))}
          </div>
        </Block>
      ) : null}

      {showRest ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Block title="Taxes" dark={dark}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    {settings?.taxes?.label || "VAT / MwSt."}
                  </p>
                  <p className={`mt-1 text-xs ${muted}`}>
                    {settings?.taxes?.note || "R3.3.4"}
                  </p>
                </div>
                <StatusPill status={settings?.taxes?.status} dark={dark} />
              </div>
            </Block>
            <Block title="Currencies" dark={dark}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    Primary: {settings?.currencies?.primary || "EUR"}
                  </p>
                  <p className={`mt-1 text-xs ${muted}`}>
                    {settings?.currencies?.note || "R3.3"}
                  </p>
                </div>
                <StatusPill status={settings?.currencies?.status} dark={dark} />
              </div>
            </Block>
            <Block title="Email" dark={dark}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    {settings?.email?.label || "Transactional email"}
                  </p>
                  <p className={`mt-1 text-xs ${muted}`}>
                    {settings?.email?.note || "R3.3"}
                  </p>
                </div>
                <StatusPill status={settings?.email?.status} dark={dark} />
              </div>
            </Block>
            <Block title="Invoices" dark={dark}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    {settings?.invoices?.label || "Invoices"}
                  </p>
                  <p className={`mt-1 text-xs ${muted}`}>
                    {settings?.invoices?.note || "R3.3.4"}
                  </p>
                </div>
                <StatusPill status={settings?.invoices?.status} dark={dark} />
              </div>
            </Block>
          </div>
        </>
      ) : null}
    </div>
  );
}
