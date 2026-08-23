"use client";

import { useState } from "react";

export type IntegrationConnection = {
  id: string;
  category?: string;
  label: string;
  status: string;
  account?: string | null;
  last_sync_at?: string | null;
  last_sync_label?: string | null;
  phase?: string;
  connectable?: boolean;
  coming?: string | null;
  note?: string | null;
  error?: string | null;
  actions?: string[];
  connect_mode?: string | null;
  oauth_ready?: boolean;
  oauth_mock?: boolean;
  stripe_user_id?: string | null;
  services_count?: number | null;
  last_test?: {
    ok?: boolean;
    to?: string;
    sent_at?: string;
    status?: string;
    title?: string;
    reason?: string;
  } | null;
  last_test_label?: string | null;
};

type Props = {
  connection: IntegrationConnection;
  dark?: boolean;
  busy?: boolean;
  onConnect: (id: string, account?: string) => void | Promise<void>;
  onDisconnect: (id: string) => void | Promise<void>;
  onReconnect: (id: string, account?: string) => void | Promise<void>;
  onSync?: (id: string) => void | Promise<void>;
  /** OAuth providers (Stripe Connect) — full-page redirect start. */
  onOAuthConnect?: (id: string) => void | Promise<void>;
  /** SMTP form providers — open credential panel. */
  onSmtpConnect?: (id: string) => void | Promise<void>;
  onTestEmail?: (id: string) => void | Promise<void>;
  /** Shipping API carriers — open credential panel. */
  onShippingConnect?: (id: string) => void | Promise<void>;
  onCreateShipment?: (id: string) => void | Promise<void>;
  onTrack?: (id: string) => void | Promise<void>;
};

const SHIPPING_API_IDS = ["dhl", "dpd", "gls", "hermes", "ups", "fedex"];

/**
 * Unified Integrations card — same UX for Stripe, PayPal, DHL, Gmail, …
 */
export function IntegrationConnectionCard({
  connection: c,
  dark = true,
  busy,
  onConnect,
  onDisconnect,
  onReconnect,
  onSync,
  onOAuthConnect,
  onSmtpConnect,
  onTestEmail,
  onShippingConnect,
  onCreateShipment,
  onTrack,
}: Props) {
  const [account, setAccount] = useState("");
  const [openForm, setOpenForm] = useState(false);
  const connected = c.status === "connected";
  const coming = c.status === "coming" || Boolean(c.coming && !c.connectable);
  const isOAuth = c.connect_mode === "oauth" || c.id === "stripe";
  const isSmtpForm =
    c.connect_mode === "smtp_form" ||
    ["gmail", "outlook", "microsoft365", "smtp"].includes(c.id);
  const isShippingApi =
    c.connect_mode === "shipping_api" || SHIPPING_API_IDS.includes(c.id);
  const needsAccount = ["paypal", "klarna", "sepa", "telegram"].includes(c.id);

  const statusLabel = coming
    ? `Coming ${c.coming || ""}`.trim()
    : connected
      ? "Connected"
      : c.status === "error"
        ? "Error"
        : "Not connected";

  const btnPrimary = dark
    ? "bg-emerald-500/90 text-black hover:bg-emerald-400"
    : "bg-emerald-700 text-white";
  const btnGhost = dark
    ? "border border-white/15 hover:bg-white/5"
    : "border border-slate-200";

  return (
    <article
      className={`rounded-2xl border p-4 ${
        dark ? "border-white/10 bg-black/20" : "border-slate-200 bg-white"
      }`}
      data-integration-id={c.id}
      data-connect-mode={c.connect_mode || "manual"}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold tracking-tight">{c.label}</h3>
          {c.phase ? (
            <p
              className={`mt-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                dark ? "text-zinc-500" : "text-slate-400"
              }`}
            >
              {c.phase}
            </p>
          ) : null}
        </div>
        <span
          className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
            connected
              ? dark
                ? "bg-emerald-500/20 text-emerald-200"
                : "bg-emerald-100 text-emerald-800"
              : coming
                ? dark
                  ? "bg-white/5 text-zinc-500"
                  : "bg-slate-100 text-slate-500"
                : dark
                  ? "bg-amber-500/15 text-amber-200"
                  : "bg-amber-50 text-amber-800"
          }`}
        >
          {statusLabel}
        </span>
      </div>

      <dl className={`mt-3 space-y-1.5 text-xs ${dark ? "text-zinc-400" : "text-slate-600"}`}>
        <div className="flex justify-between gap-3">
          <dt>Account</dt>
          <dd className={`truncate font-medium ${dark ? "text-zinc-200" : "text-slate-900"}`}>
            {c.account || "—"}
          </dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Last sync</dt>
          <dd className={`font-medium ${dark ? "text-zinc-200" : "text-slate-900"}`}>
            {c.last_sync_label || "—"}
          </dd>
        </div>
        {c.last_test_label || c.last_test ? (
          <div className="flex justify-between gap-3">
            <dt>Last Test</dt>
            <dd
              className={`font-medium ${
                c.last_test?.ok === false
                  ? "text-rose-300"
                  : dark
                    ? "text-zinc-200"
                    : "text-slate-900"
              }`}
            >
              {c.last_test_label || (c.last_test?.ok ? "Success" : "—")}
            </dd>
          </div>
        ) : null}
        {typeof c.services_count === "number" ? (
          <div className="flex justify-between gap-3">
            <dt>Services</dt>
            <dd className={`font-medium ${dark ? "text-zinc-200" : "text-slate-900"}`}>
              {c.services_count}
            </dd>
          </div>
        ) : null}
      </dl>

      {c.note ? (
        <p className={`mt-2 text-[11px] leading-relaxed ${dark ? "text-zinc-500" : "text-slate-500"}`}>
          {c.note}
        </p>
      ) : null}
      {c.error ? <p className="mt-2 text-[11px] text-rose-400">{c.error}</p> : null}

      {!coming && c.connectable !== false ? (
        <div className="mt-3 space-y-2">
          {isOAuth ? (
            <div className="flex flex-wrap gap-2">
              {!connected ? (
                <button
                  type="button"
                  disabled={busy || c.oauth_ready === false}
                  className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${btnPrimary}`}
                  onClick={() => void (onOAuthConnect ? onOAuthConnect(c.id) : onConnect(c.id))}
                >
                  {c.oauth_mock ? "Connect Stripe (mock)" : "Connect with Stripe"}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                    onClick={() => void (onOAuthConnect ? onOAuthConnect(c.id) : onReconnect(c.id))}
                  >
                    Reconnect
                  </button>
                  {onSync ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                      onClick={() => void onSync(c.id)}
                    >
                      Sync
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${
                      dark ? "text-rose-300 hover:bg-rose-500/10" : "text-rose-700"
                    }`}
                    onClick={() => void onDisconnect(c.id)}
                  >
                    Disconnect
                  </button>
                </>
              )}
            </div>
          ) : isSmtpForm ? (
            <div className="flex flex-wrap gap-2">
              {!connected || c.status === "error" ? (
                <button
                  type="button"
                  disabled={busy}
                  className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnPrimary}`}
                  onClick={() => void (onSmtpConnect ? onSmtpConnect(c.id) : onConnect(c.id))}
                >
                  Connect
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                    onClick={() => void (onSmtpConnect ? onSmtpConnect(c.id) : onReconnect(c.id))}
                  >
                    Reconnect
                  </button>
                  {onTestEmail ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnPrimary}`}
                      onClick={() => void onTestEmail(c.id)}
                    >
                      Send Test Email
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${
                      dark ? "text-rose-300 hover:bg-rose-500/10" : "text-rose-700"
                    }`}
                    onClick={() => void onDisconnect(c.id)}
                  >
                    Disconnect
                  </button>
                </>
              )}
            </div>
          ) : isShippingApi ? (
            <div className="flex flex-wrap gap-2">
              {!connected || c.status === "error" ? (
                <button
                  type="button"
                  disabled={busy}
                  className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnPrimary}`}
                  onClick={() =>
                    void (onShippingConnect ? onShippingConnect(c.id) : onConnect(c.id))
                  }
                >
                  Connect
                </button>
              ) : (
                <>
                  {onCreateShipment ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnPrimary}`}
                      onClick={() => void onCreateShipment(c.id)}
                    >
                      Create Shipment
                    </button>
                  ) : null}
                  {onTrack ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                      onClick={() => void onTrack(c.id)}
                    >
                      Track
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                    onClick={() =>
                      void (onShippingConnect ? onShippingConnect(c.id) : onReconnect(c.id))
                    }
                  >
                    Reconnect
                  </button>
                  {onSync ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                      onClick={() => void onSync(c.id)}
                    >
                      Sync
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${
                      dark ? "text-rose-300 hover:bg-rose-500/10" : "text-rose-700"
                    }`}
                    onClick={() => void onDisconnect(c.id)}
                  >
                    Disconnect
                  </button>
                </>
              )}
            </div>
          ) : openForm || (needsAccount && !connected) ? (
            <div className="space-y-2">
              {needsAccount ? (
                <input
                  value={account}
                  onChange={(e) => setAccount(e.target.value)}
                  placeholder="Account email or ID"
                  className={`w-full rounded-xl border px-3 py-2 text-sm outline-none ${
                    dark
                      ? "border-white/10 bg-black/40 text-white"
                      : "border-slate-200 bg-white text-slate-900"
                  }`}
                />
              ) : null}
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy || (needsAccount && !account.trim() && !connected)}
                  className={`rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50 ${btnPrimary}`}
                  onClick={() => {
                    void (connected
                      ? onReconnect(c.id, account.trim() || undefined)
                      : onConnect(c.id, account.trim() || undefined));
                    setOpenForm(false);
                  }}
                >
                  {connected ? "Reconnect" : "Connect"}
                </button>
                {openForm ? (
                  <button
                    type="button"
                    className={`rounded-xl px-3 py-2 text-xs ${
                      dark ? "text-zinc-400 hover:bg-white/5" : "text-slate-500"
                    }`}
                    onClick={() => setOpenForm(false)}
                  >
                    Cancel
                  </button>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {connected ? (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                    onClick={() => {
                      if (needsAccount) setOpenForm(true);
                      else void onReconnect(c.id);
                    }}
                  >
                    Reconnect
                  </button>
                  {onSync ? (
                    <button
                      type="button"
                      disabled={busy}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnGhost}`}
                      onClick={() => void onSync(c.id)}
                    >
                      Sync
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={busy}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold ${
                      dark ? "text-rose-300 hover:bg-rose-500/10" : "text-rose-700"
                    }`}
                    onClick={() => void onDisconnect(c.id)}
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  className={`rounded-xl px-3 py-2 text-xs font-semibold ${btnPrimary}`}
                  onClick={() => {
                    if (needsAccount) setOpenForm(true);
                    else void onConnect(c.id);
                  }}
                >
                  Connect
                </button>
              )}
            </div>
          )}
        </div>
      ) : null}
    </article>
  );
}
